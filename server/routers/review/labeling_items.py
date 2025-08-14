"""Labeling items endpoints for the configured review app.

These endpoints automatically use the review app associated with the configured experiment,
eliminating the need to pass review_app_id in every request.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from server.models.review_apps import Item, ListItemsResponse
from server.utils.config import get_config
from server.utils.labeling_items_utils import labeling_items_utils
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
  """List items in a labeling session.

  Returns only item state data without trace content.
  UI should fetch trace data separately via /search-traces endpoint.
  """
  review_app_id = await get_cached_review_app_id()

  # Simply return items without any trace fetching or merging
  response = await labeling_items_utils.list_items(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    filter_string=filter,
    page_size=page_size,
    page_token=page_token,
  )

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
