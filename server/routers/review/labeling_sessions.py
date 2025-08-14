"""Labeling sessions endpoints for the configured review app.

These endpoints automatically use the review app associated with the configured experiment,
eliminating the need to pass review_app_id in every request.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from server.middleware.auth import get_username, is_user_developer
from server.models.review_apps import (
  LabelingSession,
  LinkTracesToSessionRequest,
  LinkTracesToSessionResponse,
)
from server.utils.config import get_config
from server.utils.labeling_sessions_utils import (
  create_labeling_session as utils_create_session,
  delete_labeling_session as utils_delete_session,
  get_labeling_session as utils_get_session,
  link_traces_to_session as utils_link_traces,
  list_labeling_sessions as utils_list_sessions,
  update_labeling_session as utils_update_session,
)
from server.utils.permissions import check_labeling_session_access
from server.utils.review_apps_utils import review_apps_utils

router = APIRouter(prefix='/labeling-sessions', tags=['Labeling Sessions'])


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
