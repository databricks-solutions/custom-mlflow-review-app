"""MLflow proxy endpoints.

This module provides FastAPI endpoints that proxy requests to MLflow APIs,
handling authentication and providing type-safe interfaces.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.exceptions import MLflowError, NotFoundError
from server.models.mlflow import (
  CreateRunRequest,
  LinkTracesResponse,
  LogExpectationRequest,
  LogExpectationResponse,
  LogFeedbackRequest,
  LogFeedbackResponse,
  SearchRunsRequest,
  SearchRunsResponse,
  UpdateExpectationRequest,
  UpdateExpectationResponse,
  UpdateFeedbackRequest,
  UpdateFeedbackResponse,
  UpdateRunRequest,
)
from server.models.traces import (
  LinkTracesToRunRequest,
  SearchTracesRequest,
  SearchTracesResponse,
  Trace,
)
from server.utils.mlflow_utils import _extract_request_response_preview
from server.utils.mlflow_utils import (
  create_run as mlflow_create_run,
)
from server.utils.mlflow_utils import (
  get_run as mlflow_get_run,
)
from server.utils.mlflow_utils import (
  get_trace as mlflow_get_trace,
)
from server.utils.mlflow_utils import (
  get_trace_data as mlflow_get_trace_data,
)
from server.utils.mlflow_utils import (
  link_traces_to_run as mlflow_link_traces_to_run,
)
from server.utils.mlflow_utils import (
  log_expectation as mlflow_log_expectation,
)
from server.utils.mlflow_utils import (
  log_feedback as mlflow_log_feedback,
)
from server.utils.mlflow_utils import (
  search_runs as mlflow_search_runs,
)
from server.utils.mlflow_utils import (
  search_traces as mlflow_search_traces,
)
from server.utils.mlflow_utils import (
  update_expectation as mlflow_update_expectation,
)
from server.utils.mlflow_utils import (
  update_feedback as mlflow_update_feedback,
)
from server.utils.mlflow_utils import (
  update_run as mlflow_update_run,
)

router = APIRouter(prefix='/mlflow', tags=['MLflow'])


def _convert_span(span):
  """Convert MLflow span to API format."""
  return {
    'name': span.name,
    'span_id': span.span_id,
    'parent_id': span.parent_id,
    'start_time_ms': int(span.start_time_ns // 1_000_000) if span.start_time_ns else 0,
    'end_time_ms': int(span.end_time_ns // 1_000_000) if span.end_time_ns else 0,
    'status': {
      'status_code': 'OK' if span.status == 'OK' or not span.status else 'ERROR',
      'description': getattr(span, 'status_message', ''),
    },
    'span_type': getattr(span, 'span_type', 'UNKNOWN'),
    'inputs': getattr(span, 'inputs', None),
    'outputs': getattr(span, 'outputs', None),
    'attributes': getattr(span, 'attributes', None),
  }


def _convert_assessment(assessment):
  """Convert MLflow assessment to API format."""
  import logging

  logger = logging.getLogger(__name__)

  # Get assessment value and type from nested structure
  value = None
  assessment_type = None

  # FIRST: Get assessment_id from the top-level assessment object (it's always there)
  assessment_id = getattr(assessment, 'assessment_id', None)

  # Check for feedback/expectation nested structure
  if hasattr(assessment, 'feedback') and assessment.feedback:
    value = getattr(assessment.feedback, 'value', None)
    assessment_type = 'feedback'
  elif hasattr(assessment, 'expectation') and assessment.expectation:
    value = getattr(assessment.expectation, 'value', None)
    assessment_type = 'expectation'
  elif hasattr(assessment, 'value'):
    value = assessment.value
    # Try to infer type from the assessment itself
    if hasattr(assessment, 'type'):
      assessment_type = assessment.type
    elif hasattr(assessment, '__class__'):
      class_name = assessment.__class__.__name__.lower()
      if 'feedback' in class_name:
        assessment_type = 'feedback'
      elif 'expectation' in class_name:
        assessment_type = 'expectation'

  # Skip if no value
  if value is None:
    return None

  result = {
    'name': getattr(assessment, 'name', ''),
    'value': value,
    'type': assessment_type,
    'assessment_id': assessment_id,
  }

  # Add optional fields
  if hasattr(assessment, 'metadata') and assessment.metadata:
    result['metadata'] = assessment.metadata
    # Check for rationale in metadata
    if isinstance(assessment.metadata, dict) and 'rationale' in assessment.metadata:
      result['rationale'] = assessment.metadata.get('rationale')

  # Also check for rationale as a direct attribute
  if not result.get('rationale') and hasattr(assessment, 'rationale'):
    result['rationale'] = getattr(assessment, 'rationale', None)

  if hasattr(assessment, 'source') and assessment.source:
    source = assessment.source
    if hasattr(source, 'source_type') and hasattr(source, 'source_id'):
      result['source'] = {
        'source_type': source.source_type,
        'source_id': source.source_id,
      }
    else:
      result['source'] = str(source)

  return result if result.get('name') else None


def _convert_traces_to_api_format(traces, include_spans: bool = False):
  """Convert raw MLflow Trace objects to API format."""
  trace_list = []

  for trace in traces:
    try:
      request_preview, response_preview = _extract_request_response_preview(trace)

      # Build trace info
      trace_info = {
        'trace_id': trace.info.trace_id,
        'trace_location': {
          'experiment_id': trace.info.experiment_id,
          'run_id': getattr(trace.info, 'run_id', ''),
        },
        'request_time': str(trace.info.timestamp_ms),
        'execution_duration': f'{trace.info.execution_time_ms or 0}ms',
        'state': trace.info.status or 'OK',
        'trace_metadata': dict(trace.info.request_metadata or {}),
        'tags': dict(trace.info.tags or {}),
        'assessments': [],
        'request_preview': request_preview,
        'response_preview': response_preview,
      }

      # Add spans if requested
      trace_data = {'spans': []}
      if include_spans and trace.data and trace.data.spans:
        trace_data['spans'] = [_convert_span(span) for span in trace.data.spans]

      # Add assessments
      if hasattr(trace.info, 'assessments') and trace.info.assessments:
        for assessment in trace.info.assessments:
          converted = _convert_assessment(assessment)
          if converted:
            trace_info['assessments'].append(converted)

      trace_list.append({'info': trace_info, 'data': trace_data})
    except Exception:
      continue  # Skip traces that can't be converted

  return {
    'traces': trace_list,
    'next_page_token': None,
  }


@router.post('/search-traces', response_model=SearchTracesResponse)
async def search_traces(request: SearchTracesRequest) -> SearchTracesResponse:
  """Search for traces in MLflow experiments.

  Uses MLflow SDK since there's no direct API endpoint.
  """
  try:
    # Get raw traces from the simplified search_traces function
    raw_traces = mlflow_search_traces(
      experiment_ids=request.experiment_ids,
      filter_string=request.filter,
      run_id=request.run_id,
      max_results=request.max_results,
      order_by=request.order_by,
    )

    # Convert to API format
    result = _convert_traces_to_api_format(raw_traces, request.include_spans)
    return SearchTracesResponse(**result)
  except Exception as e:
    raise MLflowError(str(e), operation='search_traces')


@router.get('/runs/{run_id}')
async def get_run(run_id: str) -> Dict[str, Any]:
  """Get run details by ID."""
  return mlflow_get_run(run_id)


@router.post('/runs/create')
async def create_run(request: CreateRunRequest) -> Dict[str, Any]:
  """Create a new MLflow run."""
  return mlflow_create_run(request.dict(exclude_none=True))


@router.post('/runs/update')
async def update_run(request: UpdateRunRequest) -> Dict[str, str]:
  """Update an MLflow run."""
  mlflow_update_run(request.dict(exclude_none=True))
  return {'status': 'success'}


@router.post('/runs/search', response_model=SearchRunsResponse)
async def search_runs(request: SearchRunsRequest) -> SearchRunsResponse:
  """Search for runs in experiments."""
  result = mlflow_search_runs(request.dict(exclude_none=True))
  return SearchRunsResponse(**result)


@router.post('/traces/link-to-run', response_model=LinkTracesResponse)
async def link_traces_to_run(request: LinkTracesToRunRequest) -> LinkTracesResponse:
  """Link traces to an MLflow run.

  Note: For labeling sessions, use the combined endpoint at:
  POST /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/link-traces

  This endpoint only handles MLflow trace linking, not labeling session item creation.
  """
  result = mlflow_link_traces_to_run(
    run_id=request.run_id,
    trace_ids=request.trace_ids,
  )
  return LinkTracesResponse(
    success=True, linked_count=len(request.trace_ids), message=result.get('message')
  )


@router.get('/traces/{trace_id}', response_model=Trace)
async def get_trace(trace_id: str, run_id: str = None) -> Trace:
  """Get trace information by ID.

  Args:
      trace_id: The trace ID
      run_id: Optional run ID to help locate the trace
  """
  import logging

  logger = logging.getLogger(__name__)
  logger.info(f'🔍 [API] get_trace called with trace_id={trace_id}, run_id={run_id}')

  try:
    # If run_id is provided, search for the trace in that specific run first
    if run_id:
      logger.info(f'🔍 [API] Searching for trace {trace_id} in run {run_id}')
      raw_traces = mlflow_search_traces(
        experiment_ids=None,  # Will be inferred from run_id
        run_id=run_id,
        max_results=100,
      )

      # Find the specific trace in the results and convert to API format
      for raw_trace in raw_traces:
        if raw_trace.info.trace_id == trace_id:
          logger.info(f'✅ [API] Found trace {trace_id} via search')
          # Convert raw trace to API format
          converted_trace = _convert_traces_to_api_format([raw_trace], include_spans=True)
          return Trace(**converted_trace['traces'][0])

      logger.warning(f'⚠️ [API] Trace {trace_id} not found in run {run_id} search results')

    # Otherwise fall back to direct get_trace
    logger.info(f'🔍 [API] Attempting direct get_trace for {trace_id}')
    raw_trace = mlflow_get_trace(trace_id)

    # Convert raw trace to API format
    converted_trace = _convert_traces_to_api_format([raw_trace], include_spans=True)
    trace_data = converted_trace['traces'][0]

    # Add the required trace_location field if missing
    if 'trace_location' not in trace_data['info']:
      trace_data['info']['trace_location'] = {
        'experiment_id': raw_trace.info.experiment_id,
        'run_id': run_id or '',
      }

    return Trace(**trace_data)
  except Exception as e:
    logger.error(f'❌ [API] Failed to get trace {trace_id}: {str(e)}')
    raise NotFoundError('Trace', trace_id)


@router.get('/traces/{trace_id}/data')
async def get_trace_data(trace_id: str) -> Dict[str, Any]:
  """Get trace data (spans) by trace ID."""
  return mlflow_get_trace_data(trace_id)


@router.get('/traces/{trace_id}/metadata')
async def get_trace_metadata(trace_id: str) -> Dict[str, Any]:
  """Get trace metadata (info and spans without heavy inputs/outputs)."""
  try:
    # Get the raw trace
    raw_trace = mlflow_get_trace(trace_id)

    # Convert to API format to get proper structure
    converted_trace = _convert_traces_to_api_format([raw_trace], include_spans=True)
    trace_data = converted_trace['traces'][0]

    # Extract metadata (remove heavy inputs/outputs from spans)
    metadata = {'info': trace_data['info'], 'spans': []}

    # Process spans to keep only name and type
    for span in trace_data['data']['spans']:
      span_metadata = {
        'name': span['name'],
        'type': span.get('attributes', {}).get('mlflow.spanType', span.get('span_type', 'UNKNOWN')),
      }
      metadata['spans'].append(span_metadata)

    return metadata

  except Exception as e:
    raise HTTPException(status_code=404, detail=str(e))


@router.post('/traces/{trace_id}/feedback', response_model=LogFeedbackResponse)
async def log_trace_feedback(trace_id: str, request: LogFeedbackRequest) -> LogFeedbackResponse:
  """Log feedback on a trace.

  Args:
      trace_id: The trace ID to log feedback for
      request: The feedback request containing key, value, and optional comment

  Returns:
      LogFeedbackResponse indicating success or failure
  """
  try:
    # Get username from user_utils for now (will eventually come from middleware)
    from server.utils.user_utils import user_utils

    try:
      username = user_utils.get_username()
    except Exception:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'

    result = mlflow_log_feedback(
      trace_id=trace_id,
      key=request.assessment.name,
      value=request.assessment.value,
      username=username,
      rationale=request.assessment.rationale,
    )
    return LogFeedbackResponse(**result)
  except Exception as e:
    raise MLflowError(
      f'Failed to log feedback for trace {trace_id}: {str(e)}', operation='log_feedback'
    )


@router.post('/traces/{trace_id}/expectation', response_model=LogExpectationResponse)
async def log_trace_expectation(
  trace_id: str, request: LogExpectationRequest
) -> LogExpectationResponse:
  """Log expectation on a trace.

  Args:
      trace_id: The trace ID to log expectation for
      request: The expectation request containing key, value, and optional comment

  Returns:
      LogExpectationResponse indicating success or failure
  """
  try:
    # Get username from user_utils for now (will eventually come from middleware)
    from server.utils.user_utils import user_utils

    try:
      username = user_utils.get_username()
    except Exception:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'

    result = mlflow_log_expectation(
      trace_id=trace_id,
      key=request.assessment.name,
      value=request.assessment.value,
      username=username,
      rationale=request.assessment.rationale,
    )
    return LogExpectationResponse(**result)
  except Exception as e:
    raise MLflowError(
      f'Failed to log expectation for trace {trace_id}: {str(e)}', operation='log_expectation'
    )


@router.patch('/traces/{trace_id}/feedback', response_model=UpdateFeedbackResponse)
async def update_trace_feedback(
  trace_id: str, request: UpdateFeedbackRequest
) -> UpdateFeedbackResponse:
  """Update existing feedback on a trace.

  Args:
      trace_id: The trace ID to update feedback for
      request: The update request containing assessment_id, value, and optional rationale

  Returns:
      UpdateFeedbackResponse indicating success or failure
  """
  try:
    # Get username from user_utils for now (will eventually come from middleware)
    from server.utils.user_utils import user_utils

    try:
      username = user_utils.get_username()
    except Exception:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'

    result = mlflow_update_feedback(
      trace_id=trace_id,
      assessment_id=request.assessment_id,
      value=request.assessment.value,
      username=username,
      rationale=request.assessment.rationale,
      metadata=request.assessment.metadata,
    )
    return UpdateFeedbackResponse(**result)
  except Exception as e:
    raise MLflowError(
      f'Failed to update feedback for trace {trace_id}: {str(e)}', operation='update_feedback'
    )


@router.patch('/traces/{trace_id}/expectation', response_model=UpdateExpectationResponse)
async def update_trace_expectation(
  trace_id: str, request: UpdateExpectationRequest
) -> UpdateExpectationResponse:
  """Update existing expectation on a trace.

  Args:
      trace_id: The trace ID to update expectation for
      request: The update request containing assessment_id, value, and optional rationale

  Returns:
      UpdateExpectationResponse indicating success or failure
  """
  try:
    # Get username from user_utils for now (will eventually come from middleware)
    from server.utils.user_utils import user_utils

    try:
      username = user_utils.get_username()
    except Exception:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'

    result = mlflow_update_expectation(
      trace_id=trace_id,
      assessment_id=request.assessment_id,
      value=request.assessment.value,
      username=username,
      rationale=request.assessment.rationale,
      metadata=request.assessment.metadata,
    )
    return UpdateExpectationResponse(**result)
  except Exception as e:
    raise MLflowError(
      f'Failed to update expectation for trace {trace_id}: {str(e)}', operation='update_expectation'
    )
