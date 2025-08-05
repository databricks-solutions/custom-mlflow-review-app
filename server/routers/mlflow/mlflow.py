"""MLflow proxy endpoints.

This module provides FastAPI endpoints that proxy requests to MLflow APIs,
handling authentication and providing type-safe interfaces.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.exceptions import MLflowError, NotFoundError
from server.models.mlflow import (
  CreateRunRequest,
  CreateRunResponse,
  GetExperimentResponse,
  GetRunResponse,
  LinkTracesResponse,
  LogExpectationRequest,
  LogExpectationResponse,
  LogFeedbackRequest,
  LogFeedbackResponse,
  SearchRunsRequest,
  SearchRunsResponse,
  UpdateRunRequest,
)
from server.models.traces import (
  LinkTracesToRunRequest,
  SearchTracesRequest,
  SearchTracesResponse,
  Trace,
)
from server.utils.mlflow_utils import mlflow_utils

router = APIRouter(prefix='/mlflow', tags=['MLflow'])


@router.post('/search-traces', response_model=SearchTracesResponse)
async def search_traces(request: SearchTracesRequest) -> SearchTracesResponse:
  """Search for traces in MLflow experiments.

  Uses MLflow SDK since there's no direct API endpoint.
  """
  try:
    result = mlflow_utils.search_traces(
      experiment_ids=request.experiment_ids,
      filter_string=request.filter,
      run_id=request.run_id,
      max_results=request.max_results,
      order_by=request.order_by,
      page_token=request.page_token,
      include_spans=request.include_spans,
    )
    return SearchTracesResponse(**result)
  except Exception as e:
    raise MLflowError(str(e), operation='search_traces')


@router.get('/experiments/{experiment_id}', response_model=GetExperimentResponse)
async def get_experiment(experiment_id: str) -> GetExperimentResponse:
  """Get experiment details by ID."""
  result = mlflow_utils.get_experiment(experiment_id)
  return GetExperimentResponse(**result)


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


@router.get('/traces/{trace_id}', response_model=Trace)
async def get_trace(trace_id: str, run_id: str = None) -> Trace:
  """Get trace information by ID.
  
  Args:
      trace_id: The trace ID
      run_id: Optional run ID to help locate the trace
  """
  import logging
  logger = logging.getLogger(__name__)
  
  logger.info(f"🔍 [API] get_trace called with trace_id={trace_id}, run_id={run_id}")
  
  try:
    # If run_id is provided, search for the trace in that specific run
    if run_id:
      logger.info(f"🔍 [API] Searching for trace {trace_id} in run {run_id}")
      traces_result = mlflow_utils.search_traces(
        experiment_ids=None,  # Will be inferred from run_id
        run_id=run_id,
        max_results=100,
        include_spans=True
      )
      
      # Find the specific trace in the results
      for trace in traces_result.get('traces', []):
        if trace['info']['trace_id'] == trace_id:
          logger.info(f"✅ [API] Found trace {trace_id} via search")
          return Trace(**trace)
      
      logger.warning(f"⚠️ [API] Trace {trace_id} not found in run {run_id} search results")
    
    # Otherwise fall back to direct get_trace
    logger.info(f"🔍 [API] Attempting direct get_trace for {trace_id}")
    result = mlflow_utils.get_trace(trace_id)
    
    # The get_trace method returns a different structure, we need to transform it
    # to match our Trace model which expects trace_location field
    trace_info = result['info'].copy()
    
    # Add the required trace_location field
    trace_info['trace_location'] = {
      'experiment_id': trace_info.get('experiment_id', ''),
      'run_id': run_id or '',  # Use provided run_id or empty string
    }
    
    # Ensure other required fields have defaults
    trace_info['state'] = trace_info.get('state', 'OK')
    trace_info['trace_metadata'] = {}
    trace_info['tags'] = {}
    trace_info['assessments'] = []
    trace_info['request_preview'] = None
    trace_info['response_preview'] = None
    
    # Transform the response to match our model
    transformed_result = {
      'info': trace_info,
      'data': result.get('data', {'spans': []})
    }
    
    return Trace(**transformed_result)
  except Exception as e:
    logger.error(f"❌ [API] Failed to get trace {trace_id}: {str(e)}")
    raise NotFoundError('Trace', trace_id)


@router.get('/traces/{trace_id}/data')
async def get_trace_data(trace_id: str) -> Dict[str, Any]:
  """Get trace data (spans) by trace ID."""
  return mlflow_utils.get_trace_data(trace_id)


@router.get('/traces/{trace_id}/metadata')
async def get_trace_metadata(trace_id: str) -> Dict[str, Any]:
  """Get trace metadata (info and spans without heavy inputs/outputs)."""
  try:
    # Get the full trace data
    trace_data = mlflow_utils.get_trace(trace_id)

    # Extract metadata (remove heavy inputs/outputs from spans)
    metadata = {'info': trace_data['info'], 'spans': []}

    # Process spans to keep only name and type
    for span in trace_data['data']['spans']:
      span_metadata = {
        'name': span['name'],
        'type': span.get('attributes', {}).get('mlflow.spanType', 'UNKNOWN'),
      }

      metadata['spans'].append(span_metadata)

    return metadata

  except Exception as e:
    raise HTTPException(status_code=404, detail=str(e))


@router.post('/traces/{trace_id}/feedback', response_model=LogFeedbackResponse)
async def log_trace_feedback(
  trace_id: str, request: LogFeedbackRequest
) -> LogFeedbackResponse:
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
    except Exception as e:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'
    
    result = mlflow_utils.log_feedback(
      trace_id=trace_id,
      key=request.feedback_key,
      value=request.feedback_value,
      username=username,
      comment=request.feedback_comment,
    )
    return LogFeedbackResponse(**result)
  except Exception as e:
    raise MLflowError(f'Failed to log feedback for trace {trace_id}: {str(e)}', operation='log_feedback')


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
    except Exception as e:
      # Fallback to 'unknown' if we can't get username
      username = 'unknown'
    
    result = mlflow_utils.log_expectation(
      trace_id=trace_id,
      key=request.expectation_key,
      value=request.expectation_value,
      username=username,
      comment=request.expectation_comment,
    )
    return LogExpectationResponse(**result)
  except Exception as e:
    raise MLflowError(f'Failed to log expectation for trace {trace_id}: {str(e)}', operation='log_expectation')


