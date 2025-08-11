"""Label Schema endpoints for Review Apps."""

from typing import List

from fastapi import APIRouter, Body, HTTPException

from server.models.review_apps import LabelingSchema
from server.utils.review_apps_utils import review_apps_utils

router = APIRouter(prefix='/review-apps/{review_app_id}/schemas', tags=['Label Schemas'])


@router.get('', response_model=List[LabelingSchema])
async def list_schemas(review_app_id: str) -> List[LabelingSchema]:
  """List all label schemas for a review app."""
  try:
    review_app = await review_apps_utils.get_review_app(review_app_id)
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    return review_app.get('labeling_schemas', [])
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to list schemas: {str(e)}')


@router.post('', response_model=LabelingSchema)
async def create_schema(
  review_app_id: str, schema: LabelingSchema = Body(..., description='The schema to create')
) -> LabelingSchema:
  """Create a new label schema for a review app."""
  try:
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


@router.patch('/{schema_name}', response_model=LabelingSchema)
async def update_schema(
  review_app_id: str,
  schema_name: str,
  schema_update: LabelingSchema = Body(..., description='Updated schema data'),
) -> LabelingSchema:
  """Update an existing label schema."""
  try:
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


@router.delete('/{schema_name}')
async def delete_schema(review_app_id: str, schema_name: str) -> dict:
  """Delete a label schema from a review app."""
  try:
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
