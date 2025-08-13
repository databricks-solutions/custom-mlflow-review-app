"""Simplified endpoints for labeling sessions and schemas that use the cached review app."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query, Request

from server.middleware.auth import get_username, is_user_developer
from server.models.review_apps import (
  LabelingSchema,
  LabelingSession,
  LinkTracesToSessionRequest,
  LinkTracesToSessionResponse,
)
from server.utils.config import get_config
from server.utils.labeling_sessions_utils import (
  create_labeling_session as utils_create_session,
)
from server.utils.labeling_sessions_utils import (
  delete_labeling_session as utils_delete_session,
)
from server.utils.labeling_sessions_utils import (
  get_labeling_session as utils_get_session,
)
from server.utils.labeling_sessions_utils import (
  link_traces_to_session as utils_link_traces,
)
from server.utils.labeling_sessions_utils import (
  list_labeling_sessions as utils_list_sessions,
)
from server.utils.labeling_sessions_utils import (
  update_labeling_session as utils_update_session,
)
from server.utils.permissions import check_labeling_session_access
from server.utils.review_apps_utils import review_apps_utils

# Create router without prefix - will be added when including in main router
router = APIRouter(tags=['Simplified API'])


# Helper function to get the cached review app ID
async def get_cached_review_app_id() -> str:
  """Get the review app ID for the configured experiment."""
  config = get_config()
  experiment_id = config.experiment_id

  if not experiment_id:
    raise HTTPException(status_code=404, detail='No experiment configured')

  # Try to get review app for the experiment
  review_app = await review_apps_utils.get_review_app_by_experiment(experiment_id)
  if not review_app:
    raise HTTPException(
      status_code=404, detail=f'No review app found for experiment {experiment_id}'
    )

  review_app_id = review_app.get('review_app_id')
  if not review_app_id:
    raise HTTPException(status_code=500, detail='Review app found but missing review_app_id')

  return review_app_id


# ============================================================================
# LABEL SCHEMAS ENDPOINTS
# ============================================================================


@router.get('/label-schemas', response_model=List[LabelingSchema])
async def list_label_schemas() -> List[LabelingSchema]:
  """List all label schemas for the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()
    review_app = await review_apps_utils.get_review_app(review_app_id)

    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    schemas = review_app.get('labeling_schemas', [])
    return [LabelingSchema(**schema) for schema in schemas]
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to list schemas: {str(e)}')


@router.post('/label-schemas', response_model=LabelingSchema)
async def create_label_schema(
  schema: LabelingSchema = Body(..., description='The schema to create'),
) -> LabelingSchema:
  """Create a new label schema in the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    # Get the current review app
    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    # Check if schema with same name already exists
    existing_schemas = review_app.get('labeling_schemas', [])
    if any(s.get('name') == schema.name for s in existing_schemas):
      raise HTTPException(status_code=400, detail=f'Schema with name {schema.name} already exists')

    # Add the new schema
    existing_schemas.append(schema.dict())
    review_app['labeling_schemas'] = existing_schemas

    # Save the updated review app
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return schema
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to create schema: {str(e)}')


@router.delete('/label-schemas/{schema_name}')
async def delete_label_schema(schema_name: str) -> dict:
  """Delete a label schema from the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    # Get the current review app
    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    # Find and remove the schema
    existing_schemas = review_app.get('labeling_schemas', [])
    original_count = len(existing_schemas)
    existing_schemas = [s for s in existing_schemas if s.get('name') != schema_name]

    if len(existing_schemas) == original_count:
      raise HTTPException(status_code=404, detail=f'Schema {schema_name} not found')

    # Save the updated review app
    review_app['labeling_schemas'] = existing_schemas
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return {'message': f'Schema {schema_name} deleted successfully'}
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to delete schema: {str(e)}')


@router.patch('/label-schemas/{schema_name}', response_model=LabelingSchema)
async def update_label_schema(
  schema_name: str, schema_update: LabelingSchema = Body(..., description='Updated schema data')
) -> LabelingSchema:
  """Update an existing label schema in the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    # Get the current review app
    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    # Find and update the schema
    existing_schemas = review_app.get('labeling_schemas', [])
    schema_found = False

    for i, s in enumerate(existing_schemas):
      if s.get('name') == schema_name:
        # Update the schema
        existing_schemas[i] = schema_update.dict()
        schema_found = True
        break

    if not schema_found:
      raise HTTPException(status_code=404, detail=f'Schema {schema_name} not found')

    # Save the updated review app
    review_app['labeling_schemas'] = existing_schemas
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return schema_update
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to update schema: {str(e)}')


# ============================================================================
# LABELING SESSIONS ENDPOINTS
# ============================================================================


@router.get('/labeling-sessions')
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
    # If there's no review app, return empty sessions list
    return {'labeling_sessions': [], 'next_page_token': None}

  # Get all sessions first
  result = await utils_list_sessions(
    review_app_id=review_app_id,
    filter_string=filter,
    page_size=page_size,
    page_token=page_token,
  )

  # Handle None result
  if result is None:
    return {'labeling_sessions': [], 'next_page_token': None}

  # If user is developer, return all sessions
  if is_user_developer(request):
    return result

  # If user is SME, filter to only sessions they're assigned to
  sessions = result.get('labeling_sessions', [])
  filtered_sessions = []

  for session in sessions:
    assigned_users = session.get('assigned_users', [])
    if username in assigned_users:
      filtered_sessions.append(session)

  # Update result with filtered sessions
  result['labeling_sessions'] = filtered_sessions
  return result


@router.post('/labeling-sessions', response_model=LabelingSession)
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


@router.get('/labeling-sessions/{labeling_session_id}', response_model=LabelingSession)
async def get_labeling_session(request: Request, labeling_session_id: str) -> Dict[str, Any]:
  """Get a specific labeling session.

  Users can access sessions they're assigned to or if they're developers.
  """
  username = get_username(request)
  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  review_app_id = await get_cached_review_app_id()

  # Get the session first
  session = await utils_get_session(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
  )

  # Check if user can access this session
  assigned_users = session.get('assigned_users', [])
  if not check_labeling_session_access(username, assigned_users):
    raise HTTPException(
      status_code=403,
      detail='Access denied. You must be assigned to this labeling session or be a developer.',
    )

  return session


@router.patch('/labeling-sessions/{labeling_session_id}', response_model=LabelingSession)
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


@router.delete('/labeling-sessions/{labeling_session_id}')
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


@router.post(
  '/labeling-sessions/{labeling_session_id}/link-traces', response_model=LinkTracesToSessionResponse
)
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
