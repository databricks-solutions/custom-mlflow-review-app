"""Labeling items endpoints for the configured review app.

These endpoints automatically use the review app associated with the configured experiment,
eliminating the need to pass review_app_id in every request.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from server.models.review_apps import (
  Item,
  ListItemsResponse,
)
from server.routers.mlflow.mlflow import _convert_traces_to_api_format
from server.utils.config import get_config
from server.utils.labeling_items_utils import labeling_items_utils
from server.utils.labeling_sessions_utils import get_labeling_session
from server.utils.mlflow_utils import search_traces
from server.utils.review_apps_utils import review_apps_utils

logger = logging.getLogger(__name__)

router = APIRouter(
  prefix='/labeling-sessions/{labeling_session_id}/items',
  tags=['Labeling Items'],
)


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


@router.get('', response_model=ListItemsResponse)
async def list_items(
  labeling_session_id: str,
  filter: Optional[str] = Query(None, description='Filter string (e.g., state=PENDING)'),
  page_size: int = Query(500, ge=1, le=1000),
  page_token: Optional[str] = Query(None),
) -> Dict[str, Any]:
  """List items in a labeling session."""
  review_app_id = await get_cached_review_app_id()
  
  # Get session first to get mlflow_run_id
  session = await get_labeling_session(
    review_app_id=review_app_id, labeling_session_id=labeling_session_id
  )
  mlflow_run_id = session.get('mlflow_run_id')

  # Run list_items and search_traces in parallel
  async def get_items():
    return await labeling_items_utils.list_items(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      filter_string=filter,
      page_size=page_size,
      page_token=page_token,
    )

  async def get_traces():
    if not mlflow_run_id:
      return None
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
      return await loop.run_in_executor(
        executor, 
        lambda: search_traces(experiment_ids=None, run_id=mlflow_run_id, max_results=page_size)
      )

  # Execute in parallel
  response, raw_traces = await asyncio.gather(get_items(), get_traces())

  items = response.get('items', [])
  if not items:
    return response

  # Collect trace IDs
  trace_ids = []
  for item in items:
    if item.get('source', {}).get('trace_id'):
      trace_ids.append(item['source']['trace_id'])

  trace_previews = {}
  
  if trace_ids and raw_traces:
    try:
      search_result = _convert_traces_to_api_format(raw_traces, include_spans=False)

      # Build trace_id -> preview mapping
      for trace_data in search_result.get('traces', []):
        trace_id = trace_data.get('info', {}).get('trace_id')
        if trace_id in trace_ids:
          trace_previews[trace_id] = {
            'request_preview': trace_data.get('info', {}).get('request_preview'),
            'response_preview': trace_data.get('info', {}).get('response_preview'),
            'assessments': trace_data.get('info', {}).get('assessments', []),
          }

      logger.info(f'Found previews for {len(trace_previews)}/{len(trace_ids)} traces')
    except Exception as e:
      logger.warning(f'Failed to search traces by run_id {mlflow_run_id}: {str(e)}')

  # Add preview data and assessments to items
  for item in items:
    trace_id = item.get('source', {}).get('trace_id')
    if trace_id and trace_id in trace_previews:
      item['request_preview'] = trace_previews[trace_id].get('request_preview')
      item['response_preview'] = trace_previews[trace_id].get('response_preview')

      # Convert assessments to labels format for the UI
      assessments = trace_previews[trace_id].get('assessments', [])
      labels = {}
      for assessment in assessments:
        if assessment.get('name') and assessment.get('value') is not None:
          labels[assessment['name']] = {
            'value': assessment['value'],
            'comment': assessment.get('rationale')
          }
      
      if labels:
        item['labels'] = labels

  return response


@router.post('/batchCreate')
async def batch_create_items(
  labeling_session_id: str,
  request: Dict[str, Any],
) -> Dict[str, Any]:
  """Batch create items by proxying to Databricks API."""
  review_app_id = await get_cached_review_app_id()
  return await labeling_items_utils.batch_create_items(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    items_data=request,
  )


@router.get('/{item_id}', response_model=Item)
async def get_item(
  labeling_session_id: str,
  item_id: str,
) -> Dict[str, Any]:
  """Get a specific item."""
  review_app_id = await get_cached_review_app_id()
  return await labeling_items_utils.get_item(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    item_id=item_id,
  )


@router.patch('/{item_id}', response_model=Item)
async def update_item(
  labeling_session_id: str,
  item_id: str,
  item: Item,
  update_mask: str = Query(..., description='Comma-separated list of fields to update'),
) -> Dict[str, Any]:
  """Update an item.

  Example update_mask: "state,chat_rounds"
  """
  review_app_id = await get_cached_review_app_id()
  
  try:
    logger.info(
      f'🔧 [UPDATE ITEM] Updating item {item_id} with data: {item.model_dump(exclude_unset=True)}'
    )
    data = item.model_dump(exclude_unset=True)
    result = await labeling_items_utils.update_item(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      item_id=item_id,
      item_data=data,
      update_mask=update_mask,
    )
    logger.info(f'✅ [UPDATE ITEM] Successfully updated item {item_id}')
    return result
  except Exception as e:
    logger.error(f'❌ [UPDATE ITEM] Failed to update item {item_id}: {str(e)}')
    raise


@router.delete('/{item_id}')
async def delete_item(
  labeling_session_id: str,
  item_id: str,
) -> Dict[str, Any]:
  """Delete/unlink an item from the labeling session."""
  review_app_id = await get_cached_review_app_id()
  return await labeling_items_utils.delete_item(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    item_id=item_id,
  )
