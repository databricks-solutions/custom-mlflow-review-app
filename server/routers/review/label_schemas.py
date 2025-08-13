"""Label schemas endpoints for the configured review app.

These endpoints automatically use the review app associated with the configured experiment,
eliminating the need to pass review_app_id in every request.
"""

from typing import List

from fastapi import APIRouter, Body, HTTPException

from server.models.review_apps import LabelingSchema
from server.utils.config import get_config
from server.utils.review_apps_utils import review_apps_utils

router = APIRouter(prefix='/label-schemas', tags=['Label Schemas'])


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


@router.get('', response_model=List[LabelingSchema])
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


@router.post('', response_model=LabelingSchema)
async def create_label_schema(
  schema: LabelingSchema = Body(..., description='The schema to create'),
) -> LabelingSchema:
  """Create a new label schema in the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    existing_schemas = review_app.get('labeling_schemas', [])
    if any(s.get('name') == schema.name for s in existing_schemas):
      raise HTTPException(status_code=400, detail=f'Schema with name {schema.name} already exists')

    existing_schemas.append(schema.dict())
    review_app['labeling_schemas'] = existing_schemas

    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return schema
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to create schema: {str(e)}')


@router.delete('/{schema_name}')
async def delete_label_schema(schema_name: str) -> dict:
  """Delete a label schema from the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    existing_schemas = review_app.get('labeling_schemas', [])
    original_count = len(existing_schemas)
    existing_schemas = [s for s in existing_schemas if s.get('name') != schema_name]

    if len(existing_schemas) == original_count:
      raise HTTPException(status_code=404, detail=f'Schema {schema_name} not found')

    review_app['labeling_schemas'] = existing_schemas
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return {'message': f'Schema {schema_name} deleted successfully'}
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to delete schema: {str(e)}')


@router.patch('/{schema_name}', response_model=LabelingSchema)
async def update_label_schema(
  schema_name: str, schema_update: LabelingSchema = Body(..., description='Updated schema data')
) -> LabelingSchema:
  """Update an existing label schema in the cached review app."""
  try:
    review_app_id = await get_cached_review_app_id()

    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    existing_schemas = review_app.get('labeling_schemas', [])
    schema_found = False

    for i, s in enumerate(existing_schemas):
      if s.get('name') == schema_name:
        existing_schemas[i] = schema_update.dict()
        schema_found = True
        break

    if not schema_found:
      raise HTTPException(status_code=404, detail=f'Schema {schema_name} not found')

    review_app['labeling_schemas'] = existing_schemas
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')

    return schema_update
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to update schema: {str(e)}')
