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
from server.models.traces import (
  LinkTracesToRunRequest,
  SearchTracesRequest,
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


@router.post('/search-traces')
async def search_traces(request: SearchTracesRequest) -> Dict[str, Any]:
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

    # Convert traces to dict format and return directly
    traces_list = [trace.to_dict() for trace in raw_traces]

    # Add request/response previews
    for trace, trace_dict in zip(raw_traces, traces_list):
      request_preview, response_preview = _extract_request_response_preview(trace)
      if 'info' in trace_dict:
        trace_dict['info']['request_preview'] = request_preview
        trace_dict['info']['response_preview'] = response_preview

    return {'traces': traces_list, 'next_page_token': None}
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


@router.get('/traces/{trace_id}')
async def get_trace(trace_id: str) -> Dict[str, Any]:
  """Get trace information by ID.

  Args:
      trace_id: The trace ID
  """
  try:
    # Get the trace directly using MLflow
    raw_trace = mlflow_get_trace(trace_id)

    # Convert to dict and add previews
    trace_dict = raw_trace.to_dict()
    request_preview, response_preview = _extract_request_response_preview(raw_trace)

    if 'info' in trace_dict:
      trace_dict['info']['request_preview'] = request_preview
      trace_dict['info']['response_preview'] = response_preview

    return trace_dict
  except Exception:
    raise NotFoundError('Trace', trace_id)


@router.get('/traces/{trace_id}/data')
async def get_trace_data(trace_id: str) -> Dict[str, Any]:
  """Get trace data (spans) by trace ID."""
  return mlflow_get_trace_data(trace_id)




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
