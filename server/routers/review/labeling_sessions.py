"""Labeling sessions endpoints for the configured review app.

These endpoints automatically use the review app associated with the configured experiment,
eliminating the need to pass review_app_id in every request.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel

from server.middleware.auth import get_username, is_user_developer
from server.models.review_apps import (
  LabelingSession,
  LinkTracesToSessionRequest,
  LinkTracesToSessionResponse,
)
from server.utils.config import get_config
from server.utils.labeling_session_analysis import analyze_labeling_session_complete
from server.utils.labeling_sessions_utils import (
  create_labeling_session as utils_create_session,
  delete_labeling_session as utils_delete_session,
  get_labeling_session as utils_get_session,
  link_traces_to_session as utils_link_traces,
  list_labeling_sessions as utils_list_sessions,
  update_labeling_session as utils_update_session,
)
from server.utils.mlflow_artifact_utils import MLflowArtifactManager
from server.utils.permissions import check_labeling_session_access
from server.utils.review_apps_utils import review_apps_utils

logger = logging.getLogger(__name__)


class TriggerAnalysisRequest(BaseModel):
  """Request to trigger analysis of a labeling session."""

  include_ai_insights: bool = True
  model_endpoint: str = 'databricks-claude-sonnet-4'


class AnalysisStatus(BaseModel):
  """Status of a session analysis."""

  session_id: str
  status: str  # 'pending', 'running', 'completed', 'failed', 'not_found'
  message: Optional[str] = None
  run_id: Optional[str] = None
  report_path: Optional[str] = None


router = APIRouter(prefix='/labeling-sessions', tags=['Labeling Sessions'])

# Store for tracking analysis status (in production, use database)
analysis_status_store: Dict[str, AnalysisStatus] = {}


async def get_cached_review_app_id() -> str:
  """Get the review app ID for the configured experiment."""
  config = get_config()
  experiment_id = config.experiment_id

  if not experiment_id:
    raise HTTPException(status_code=404, detail='No experiment configured')

  review_app = await review_apps_utils.get_review_app_by_experiment(experiment_id)
  if not review_app:
    raise HTTPException(
      status_code=404, detail=f'No review app found for experiment {experiment_id}'
    )

  review_app_id = review_app.get('review_app_id')
  if not review_app_id:
    raise HTTPException(status_code=500, detail='Review app found but missing review_app_id')

  return review_app_id


@router.get('')
async def list_labeling_sessions(
  request: Request,
  filter: Optional[str] = Query(None, description='Filter string'),
  page_size: int = Query(500, ge=1, le=1000),
  page_token: Optional[str] = Query(None),
) -> Dict[str, Any]:
  """List labeling sessions for the cached review app.

  Developers see all sessions, SMEs only see sessions they're assigned to.

  Common filters:
  - state=IN_PROGRESS
  - assigned_users=user@example.com
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  try:
    review_app_id = await get_cached_review_app_id()
  except HTTPException:
    return {'labeling_sessions': [], 'next_page_token': None}

  result = await utils_list_sessions(
    review_app_id=review_app_id,
    filter_string=filter,
    page_size=page_size,
    page_token=page_token,
  )

  if result is None:
    return {'labeling_sessions': [], 'next_page_token': None}

  if is_user_developer(request):
    return result

  sessions = result.get('labeling_sessions', [])
  filtered_sessions = []

  for session in sessions:
    assigned_users = session.get('assigned_users', [])
    if username in assigned_users:
      filtered_sessions.append(session)

  result['labeling_sessions'] = filtered_sessions
  return result


@router.post('', response_model=LabelingSession)
async def create_labeling_session(
  request: Request, labeling_session: LabelingSession
) -> Dict[str, Any]:
  """Create a new labeling session for the cached review app. Requires developer role."""
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  if not is_user_developer(request):
    raise HTTPException(
      status_code=403, detail='Access denied. Developer role required to create labeling sessions.'
    )

  review_app_id = await get_cached_review_app_id()

  data = labeling_session.model_dump(exclude_unset=True)
  return await utils_create_session(
    review_app_id=review_app_id,
    labeling_session_data=data,
  )


@router.get('/{labeling_session_id}', response_model=LabelingSession)
async def get_labeling_session(request: Request, labeling_session_id: str) -> Dict[str, Any]:
  """Get a specific labeling session.

  Users can access sessions they're assigned to or if they're developers.
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  review_app_id = await get_cached_review_app_id()

  session = await utils_get_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )

  assigned_users = session.get('assigned_users', [])
  if not check_labeling_session_access(username, assigned_users):
    raise HTTPException(
      status_code=403,
      detail='Access denied. You must be assigned to this labeling session or be a developer.',
    )

  return session


@router.patch('/{labeling_session_id}', response_model=LabelingSession)
async def update_labeling_session(
  request: Request,
  labeling_session_id: str,
  labeling_session: LabelingSession,
  update_mask: str = Query(..., description='Comma-separated list of fields to update'),
) -> Dict[str, Any]:
  """Update a labeling session. Requires developer role.

  Example update_mask: "name,assigned_users,labeling_schemas"
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  if not is_user_developer(request):
    raise HTTPException(
      status_code=403, detail='Access denied. Developer role required to update labeling sessions.'
    )

  review_app_id = await get_cached_review_app_id()

  data = labeling_session.model_dump(exclude_unset=True)
  return await utils_update_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    labeling_session_data=data,
    update_mask=update_mask,
  )


@router.delete('/{labeling_session_id}')
async def delete_labeling_session(request: Request, labeling_session_id: str) -> Dict[str, Any]:
  """Delete a labeling session. Requires developer role."""
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  if not is_user_developer(request):
    raise HTTPException(
      status_code=403, detail='Access denied. Developer role required to delete labeling sessions.'
    )

  review_app_id = await get_cached_review_app_id()

  return await utils_delete_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )


@router.post('/{labeling_session_id}/link-traces', response_model=LinkTracesToSessionResponse)
async def link_traces_to_session(
  request: Request, labeling_session_id: str, link_request: LinkTracesToSessionRequest
) -> LinkTracesToSessionResponse:
  """Link traces to a labeling session. Requires developer role.

  This endpoint combines two operations:
  1. Links traces to the MLflow run associated with the labeling session
  2. Creates labeling items for the traces in the session

  This ensures traces are properly linked for both MLflow tracking and labeling workflows.
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  if not is_user_developer(request):
    raise HTTPException(
      status_code=403, detail='Access denied. Developer role required to link traces to sessions.'
    )

  review_app_id = await get_cached_review_app_id()

  result = await utils_link_traces(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    mlflow_run_id=link_request.mlflow_run_id,
    trace_ids=link_request.trace_ids,
  )

  if result.get('success'):
    return LinkTracesToSessionResponse(
      success=True,
      linked_traces=result.get('linked_traces', len(link_request.trace_ids)),
      message=f'Successfully linked {result.get("linked_traces", len(link_request.trace_ids))} traces to session',
    )
  else:
    return LinkTracesToSessionResponse(
      success=False,
      linked_traces=0,
      message=result.get('error', 'Failed to link traces'),
      items_created=0,
    )


# ============================================================================
# Analysis Endpoints
# ============================================================================


@router.get('/{labeling_session_id}/analysis')
async def get_session_analysis(
  request: Request,
  labeling_session_id: str,
) -> Dict[str, Any]:
  """Retrieve analysis report for a labeling session from MLflow artifacts.

  Returns the analysis if it exists, or indicates that analysis needs to be run.
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  review_app_id = await get_cached_review_app_id()

  # Check access permissions
  session = await utils_get_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )

  assigned_users = session.get('assigned_users', [])
  if not is_user_developer(request):
    if not check_labeling_session_access(username, assigned_users):
      raise HTTPException(
        status_code=403, detail='Access denied. You are not assigned to this session.'
      )

  try:
    # Get the session's MLflow run ID
    mlflow_run_id = session.get('mlflow_run_id')
    if not mlflow_run_id:
      return {
        'has_analysis': False,
        'message': 'Session does not have an MLflow run ID',
        'session_id': labeling_session_id,
      }

    # Check for analysis artifacts
    artifact_manager = MLflowArtifactManager()

    try:
      # Try to download the report
      report_content = artifact_manager.download_analysis_report(
        run_id=mlflow_run_id, artifact_path='analysis/session_summary/report.md'
      )

      # Try to get structured data
      structured_data = None
      metadata = None
      try:
        data_content = artifact_manager.download_analysis_report(
          run_id=mlflow_run_id, artifact_path='analysis/session_summary/data.json'
        )
        import json

        structured_data = json.loads(data_content)
        metadata = structured_data.get('metadata', {})
      except Exception:
        pass

      return {
        'has_analysis': True,
        'content': report_content,
        'session_id': labeling_session_id,
        'run_id': mlflow_run_id,
        'metadata': metadata,
        'message': None,
      }

    except Exception:
      # No analysis found
      return {
        'has_analysis': False,
        'content': None,
        'session_id': labeling_session_id,
        'run_id': mlflow_run_id,
        'message': (
          'No analysis found. Click "Run Analysis" to generate insights from SME assessments.'
        ),
      }

  except Exception as e:
    logger.error(f'Error retrieving session analysis: {e}')
    raise HTTPException(status_code=500, detail=str(e))


async def run_analysis_task(
  review_app_id: str, session_id: str, include_ai: bool, model_endpoint: str
):
  """Background task to run session analysis."""
  try:
    # Update status to running
    analysis_status_store[session_id] = AnalysisStatus(
      session_id=session_id, status='running', message='Analysis in progress...'
    )

    # Run the analysis
    result = await analyze_labeling_session_complete(
      review_app_id=review_app_id,
      session_id=session_id,
      include_ai_insights=include_ai,
      model_endpoint=model_endpoint,
    )

    # Update status based on result
    if result.get('status') == 'success':
      storage = result.get('storage', {})
      analysis_status_store[session_id] = AnalysisStatus(
        session_id=session_id,
        status='completed',
        message='Analysis completed successfully',
        run_id=storage.get('run_id'),
        report_path=storage.get('report_path'),
      )
    else:
      analysis_status_store[session_id] = AnalysisStatus(
        session_id=session_id, status='failed', message=result.get('error', 'Analysis failed')
      )

  except Exception as e:
    logger.error(f'Analysis task failed: {e}')
    analysis_status_store[session_id] = AnalysisStatus(
      session_id=session_id, status='failed', message=str(e)
    )


@router.post('/{labeling_session_id}/analysis/trigger', response_model=AnalysisStatus)
async def trigger_session_analysis(
  request: Request,
  labeling_session_id: str,
  analysis_request: TriggerAnalysisRequest,
  background_tasks: BackgroundTasks,
) -> AnalysisStatus:
  """Trigger analysis of a labeling session.

  This runs the analysis in the background and returns immediately.
  The analysis will be stored in the session's MLflow run artifacts.
  Re-running will overwrite the previous analysis.
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  review_app_id = await get_cached_review_app_id()

  # Check access permissions
  session = await utils_get_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )

  assigned_users = session.get('assigned_users', [])
  if not is_user_developer(request):
    if not check_labeling_session_access(username, assigned_users):
      raise HTTPException(
        status_code=403, detail='Access denied. You are not assigned to this session.'
      )

  # Check if analysis is already running
  if labeling_session_id in analysis_status_store:
    existing_status = analysis_status_store[labeling_session_id]
    if existing_status.status == 'running':
      return existing_status

  # Initialize status
  analysis_status_store[labeling_session_id] = AnalysisStatus(
    session_id=labeling_session_id, status='pending', message='Analysis queued'
  )

  # Add background task
  background_tasks.add_task(
    run_analysis_task,
    review_app_id,
    labeling_session_id,
    analysis_request.include_ai_insights,
    analysis_request.model_endpoint,
  )

  return analysis_status_store[labeling_session_id]


@router.get('/{labeling_session_id}/analysis/status', response_model=AnalysisStatus)
async def get_analysis_status(
  request: Request,
  labeling_session_id: str,
) -> AnalysisStatus:
  """Get the status of an analysis request.

  Returns the current status of the analysis (pending, running, completed, failed).
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  review_app_id = await get_cached_review_app_id()

  # Check access permissions
  session = await utils_get_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )

  assigned_users = session.get('assigned_users', [])
  if not is_user_developer(request):
    if not check_labeling_session_access(username, assigned_users):
      raise HTTPException(
        status_code=403, detail='Access denied. You are not assigned to this session.'
      )

  if labeling_session_id not in analysis_status_store:
    return AnalysisStatus(
      session_id=labeling_session_id,
      status='not_found',
      message='No analysis request found for this session',
    )

  return analysis_status_store[labeling_session_id]
