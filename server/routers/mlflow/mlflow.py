"""MLflow proxy endpoints.

This module provides FastAPI endpoints that proxy requests to MLflow APIs,
handling authentication and providing type-safe interfaces.
"""

from typing import Any, Dict

from fastapi import APIRouter

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
from server.models.traces import LinkTracesToRunRequest, SearchTracesRequest
from server.utils import mlflow_utils

router = APIRouter(prefix='/mlflow', tags=['MLflow'])


@router.post('/search-traces')
async def search_traces(request: SearchTracesRequest) -> Dict[str, Any]:
  """Search for traces in MLflow experiments.

  Uses MLflow SDK since there's no direct API endpoint.
  """
  try:
    # Get raw traces from the simplified search_traces function
    raw_traces = mlflow_utils.search_traces(
      experiment_ids=request.experiment_ids,
      filter_string=request.filter,
      run_id=request.run_id,
      max_results=request.max_results,
      order_by=request.order_by,
    )

    # Convert traces to dict format
    traces_list = []

    # For each trace, fetch the full trace with assessments
    for trace in raw_traces:
      # Get the full trace with assessments using get_trace
      # This is necessary because search_traces doesn't return assessments
      try:
        full_trace = mlflow_utils.get_trace(trace.info.trace_id)
        trace_dict = full_trace.to_dict()
        
        # Add assessments to the dict since to_dict() doesn't include them
        if hasattr(full_trace, 'search_assessments'):
          assessments = full_trace.search_assessments()
          if assessments:
            trace_dict['assessments'] = []
            for assessment in assessments:
              # Convert assessment to dict format
              assessment_dict = {
                'assessment_id': assessment.assessment_id,
                'assessment_name': assessment.assessment_name,
                'timestamp': assessment.timestamp,
              }
              
              # Add feedback or expectation details
              if assessment.feedback:
                assessment_dict['feedback'] = {
                  'value': assessment.feedback.value,
                  'rationale': assessment.feedback.rationale if hasattr(assessment.feedback, 'rationale') else None,
                  'metadata': assessment.feedback.metadata if hasattr(assessment.feedback, 'metadata') else None,
                  'source': {
                    'source_type': assessment.feedback.source.source_type if hasattr(assessment.feedback.source, 'source_type') else 'human',
                    'source_id': assessment.feedback.source.source_id if hasattr(assessment.feedback.source, 'source_id') else None,
                  } if hasattr(assessment.feedback, 'source') else None,
                }
              elif assessment.expectation:
                assessment_dict['expectation'] = {
                  'value': assessment.expectation.value,
                  'metadata': assessment.expectation.metadata if hasattr(assessment.expectation, 'metadata') else None,
                  'source': {
                    'source_type': assessment.expectation.source.source_type if hasattr(assessment.expectation.source, 'source_type') else 'human',
                    'source_id': assessment.expectation.source.source_id if hasattr(assessment.expectation.source, 'source_id') else None,
                  } if hasattr(assessment.expectation, 'source') else None,
                }
                # For expectations, rationale is in metadata
                if assessment_dict['expectation']['metadata'] and 'rationale' in assessment_dict['expectation']['metadata']:
                  assessment_dict['metadata'] = {'rationale': assessment_dict['expectation']['metadata']['rationale']}
              
              trace_dict['assessments'].append(assessment_dict)
        
      except Exception:
        # If we can't get the full trace, use the search result
        trace_dict = trace.to_dict()

      # Add request/response previews
      request_preview, response_preview = mlflow_utils._extract_request_response_preview(trace)
      if 'info' in trace_dict:
        trace_dict['info']['request_preview'] = request_preview
        trace_dict['info']['response_preview'] = response_preview

      traces_list.append(trace_dict)

    return {'traces': traces_list, 'next_page_token': None}
  except Exception as e:
    raise MLflowError(str(e), operation='search_traces')


@router.get('/runs/{run_id}')
async def get_run(run_id: str) -> Dict[str, Any]:
  """Get run details by ID."""
  return mlflow_utils.get_run(run_id)


@router.post('/runs/create')
async def create_run(request: CreateRunRequest) -> Dict[str, Any]:
  """Create a new MLflow run."""
  return mlflow_utils.create_run(request.dict(exclude_none=True))


@router.post('/runs/update')
async def update_run(request: UpdateRunRequest) -> Dict[str, str]:
  """Update an MLflow run."""
  mlflow_utils.update_run(request.dict(exclude_none=True))
  return {'status': 'success'}


@router.post('/runs/search', response_model=SearchRunsResponse)
async def search_runs(request: SearchRunsRequest) -> SearchRunsResponse:
  """Search for runs in experiments."""
  result = mlflow_utils.search_runs(request.dict(exclude_none=True))
  return SearchRunsResponse(**result)


@router.post('/traces/link-to-run', response_model=LinkTracesResponse)
async def link_traces_to_run(request: LinkTracesToRunRequest) -> LinkTracesResponse:
  """Link traces to an MLflow run.

  Note: For labeling sessions, use the combined endpoint at:
  POST /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/link-traces

  This endpoint only handles MLflow trace linking, not labeling session item creation.
  """
  result = mlflow_utils.link_traces_to_run(
    run_id=request.run_id,
    trace_ids=request.trace_ids,
  )
  return LinkTracesResponse(
    success=True, linked_count=len(request.trace_ids), message=result.get('message')
  )


@router.get('/traces/{trace_id}')
async def get_trace(trace_id: str) -> Dict[str, Any]:
  """Get trace information by ID.

  Args:
      trace_id: The trace ID
  """
  try:
    # Get the trace directly using MLflow
    raw_trace = mlflow_utils.get_trace(trace_id)

    # Convert to dict and add previews
    trace_dict = raw_trace.to_dict()
    
    # Add assessments to the dict since to_dict() doesn't include them
    if hasattr(raw_trace, 'search_assessments'):
      assessments = raw_trace.search_assessments()
      if assessments:
        trace_dict['assessments'] = []
        for assessment in assessments:
          # Convert assessment to dict format
          assessment_dict = {
            'assessment_id': assessment.assessment_id,
            'assessment_name': assessment.assessment_name,
            'timestamp': assessment.timestamp,
          }
          
          # Add feedback or expectation details
          if assessment.feedback:
            assessment_dict['feedback'] = {
              'value': assessment.feedback.value,
              'rationale': assessment.feedback.rationale if hasattr(assessment.feedback, 'rationale') else None,
              'metadata': assessment.feedback.metadata if hasattr(assessment.feedback, 'metadata') else None,
              'source': {
                'source_type': assessment.feedback.source.source_type if hasattr(assessment.feedback.source, 'source_type') else 'human',
                'source_id': assessment.feedback.source.source_id if hasattr(assessment.feedback.source, 'source_id') else None,
              } if hasattr(assessment.feedback, 'source') else None,
            }
          elif assessment.expectation:
            assessment_dict['expectation'] = {
              'value': assessment.expectation.value,
              'metadata': assessment.expectation.metadata if hasattr(assessment.expectation, 'metadata') else None,
              'source': {
                'source_type': assessment.expectation.source.source_type if hasattr(assessment.expectation.source, 'source_type') else 'human',
                'source_id': assessment.expectation.source.source_id if hasattr(assessment.expectation.source, 'source_id') else None,
              } if hasattr(assessment.expectation, 'source') else None,
            }
            # For expectations, rationale is in metadata
            if assessment_dict['expectation']['metadata'] and 'rationale' in assessment_dict['expectation']['metadata']:
              assessment_dict['metadata'] = {'rationale': assessment_dict['expectation']['metadata']['rationale']}
          
          trace_dict['assessments'].append(assessment_dict)
    
    request_preview, response_preview = mlflow_utils._extract_request_response_preview(raw_trace)

    if 'info' in trace_dict:
      trace_dict['info']['request_preview'] = request_preview
      trace_dict['info']['response_preview'] = response_preview

    return trace_dict
  except Exception:
    raise NotFoundError('Trace', trace_id)


@router.get('/traces/{trace_id}/data')
async def get_trace_data(trace_id: str) -> Dict[str, Any]:
  """Get trace data (spans) by trace ID."""
  return mlflow_utils.get_trace_data(trace_id)


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

    result = mlflow_utils.log_feedback(
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

    result = mlflow_utils.log_expectation(
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

    result = mlflow_utils.update_feedback(
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

    result = mlflow_utils.update_expectation(
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
