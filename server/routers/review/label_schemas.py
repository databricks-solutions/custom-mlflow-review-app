"""Label Schema endpoints for Review Apps."""

import cProfile
import io
import logging
import pstats
import time
from typing import List

from fastapi import APIRouter, Body, HTTPException

from server.models.review_apps import LabelingSchema
from server.utils.review_apps_utils import review_apps_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
  total_start = time.time()
  timings = {}
  
  # Enable cProfile for this request
  profiler = cProfile.Profile()
  profiler.enable()
  
  logger.info(f'🎯 [SCHEMA CREATE] Starting schema creation for review_app_id={review_app_id}, schema_name={schema.name}')
  
  try:
    # Get the current review app
    get_start = time.time()
    review_app = await review_apps_utils.get_review_app(review_app_id)
    get_time = time.time() - get_start
    timings['get_review_app'] = get_time * 1000
    logger.info(f'⏱️ [SCHEMA CREATE] get_review_app took {get_time * 1000:.1f}ms')
    
    if not review_app:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    # Check if schema with same name already exists
    check_start = time.time()
    existing_schemas = review_app.get('labeling_schemas', [])
    if any(s.get('name') == schema.name for s in existing_schemas):
      raise HTTPException(status_code=400, detail=f'Schema with name {schema.name} already exists')
    check_time = time.time() - check_start
    timings['check_existing'] = check_time * 1000
    logger.info(f'⏱️ [SCHEMA CREATE] check_existing took {check_time * 1000:.1f}ms')

    # Add the new schema
    append_start = time.time()
    schema_dict = schema.dict()
    existing_schemas.append(schema_dict)
    review_app['labeling_schemas'] = existing_schemas
    append_time = time.time() - append_start
    timings['append_schema'] = append_time * 1000
    logger.info(f'⏱️ [SCHEMA CREATE] append_schema took {append_time * 1000:.1f}ms')
    logger.info(f'📊 [SCHEMA CREATE] Schema dict size: {len(str(schema_dict))} chars')
    logger.info(f'📊 [SCHEMA CREATE] Total schemas count: {len(existing_schemas)}')

    # Save the updated review app
    update_start = time.time()
    await review_apps_utils.update_review_app(review_app_id, review_app, 'labeling_schemas')
    update_time = time.time() - update_start
    timings['update_review_app'] = update_time * 1000
    logger.info(f'⏱️ [SCHEMA CREATE] update_review_app took {update_time * 1000:.1f}ms')

    total_time = time.time() - total_start
    timings['total'] = total_time * 1000
    
    logger.info(f'✅ [SCHEMA CREATE] Schema creation completed in {total_time * 1000:.1f}ms')
    logger.info(f'📈 [SCHEMA CREATE] Timing breakdown: {timings}')
    
    # Disable profiler and print results
    profiler.disable()
    
    # Get profiling stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Print top 30 functions
    
    # Log the most time-consuming operations
    profile_output = s.getvalue()
    lines = profile_output.split('\n')
    
    logger.info('🔬 [SCHEMA CREATE] Top time-consuming operations:')
    for line in lines:
        # Look for lines with significant time spent
        if any(keyword in line.lower() for keyword in [
            'databricks', 'mlflow', 'fetch', 'http', 'request', 
            'review_app', 'update', 'get_', 'proxy', 'auth'
        ]):
            logger.info(f'   {line.strip()}')
    
    return schema
  except HTTPException:
    profiler.disable()
    raise
  except Exception as e:
    profiler.disable()
    total_time = time.time() - total_start
    logger.error(f'❌ [SCHEMA CREATE] Failed after {total_time * 1000:.1f}ms: {str(e)}')
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
