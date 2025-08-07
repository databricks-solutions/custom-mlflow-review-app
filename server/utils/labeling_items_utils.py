"""Labeling Items utility functions for direct use as tools by Claude."""

from typing import Any, Dict, Optional

from server.utils.databricks_auth import get_managed_evals_api_url
from server.utils.proxy import fetch_databricks


class LabelingItemsUtils:
  """Utility class for Labeling Items operations that can be used directly by Claude."""

  async def list_items(
    self,
    review_app_id: str,
    labeling_session_id: str,
    filter_string: Optional[str] = None,
    page_size: int = 500,
    page_token: Optional[str] = None,
  ) -> Dict[str, Any]:
    """List items in a labeling session.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        filter_string: Filter string (e.g., state=PENDING, state=IN_PROGRESS, state=COMPLETED)
        page_size: Number of items per page (1-1000)
        page_token: Pagination token for next page

    Returns:
        Dictionary containing list of items and pagination info
    """
    params = {'page_size': page_size}
    if filter_string:
      params['filter'] = filter_string
    if page_token:
      params['page_token'] = page_token

    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items'
    )
    response = await fetch_databricks(
      method='GET',
      url=url,
      params=params,
    )

    # Handle empty response
    if not response:
      return {'items': [], 'next_page_token': None}

    # Ensure response has the expected structure
    if 'items' not in response:
      response = {'items': [], 'next_page_token': None}

    return response

  async def get_item(
    self,
    review_app_id: str,
    labeling_session_id: str,
    item_id: str,
  ) -> Dict[str, Any]:
    """Get a specific item.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        item_id: The item ID

    Returns:
        Dictionary containing item details
    """
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}'
    )
    response = await fetch_databricks(
      method='GET',
      url=url,
    )

    return response

  async def update_item(
    self,
    review_app_id: str,
    labeling_session_id: str,
    item_id: str,
    item_data: Dict[str, Any],
    update_mask: str,
  ) -> Dict[str, Any]:
    """Update an item.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        item_id: The item ID
        item_data: Updated item data
        update_mask: Comma-separated list of fields to update (e.g., "state,chat_rounds")

    Returns:
        Dictionary containing updated item
    """
    import logging

    logger = logging.getLogger(__name__)

    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}'
    )
    params = {'update_mask': update_mask}

    logger.info(f'🔧 [DATABRICKS API] Updating item via Databricks: {url}')
    logger.info(f'🔧 [DATABRICKS API] Item data: {item_data}')
    logger.info(f'🔧 [DATABRICKS API] Update mask: {update_mask}')

    try:
      response = await fetch_databricks(
        method='PATCH',
        url=url,
        data=item_data,
        params=params,
      )
      logger.info(f'✅ [DATABRICKS API] Successfully updated item {item_id}')
      return response
    except Exception as e:
      logger.error(f'❌ [DATABRICKS API] Failed to update item {item_id}: {str(e)}')
      raise

  async def label_item(
    self,
    review_app_id: str,
    labeling_session_id: str,
    item_id: str,
    labels: Dict[str, Any],
    comment: Optional[str] = None,
    state: str = 'COMPLETED',
  ) -> Dict[str, Any]:
    """Label an item with ratings and feedback.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        item_id: The item ID
        labels: Dictionary of labels/ratings to apply
        comment: Optional comment/feedback text
        state: Item state (COMPLETED, SKIPPED, etc.)

    Returns:
        Dictionary containing updated item
    """
    item_data = {
      'state': state,
      'labels': labels,
    }
    if comment:
      item_data['comment'] = comment

    return await self.update_item(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      item_id=item_id,
      item_data=item_data,
      update_mask='state,labels,comment' if comment else 'state,labels',
    )

  async def skip_item(
    self,
    review_app_id: str,
    labeling_session_id: str,
    item_id: str,
    comment: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Skip an item (mark as SKIPPED).

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        item_id: The item ID
        comment: Optional reason for skipping

    Returns:
        Dictionary containing updated item
    """
    item_data = {'state': 'SKIPPED'}
    if comment:
      item_data['comment'] = comment

    return await self.update_item(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      item_id=item_id,
      item_data=item_data,
      update_mask='state,comment' if comment else 'state',
    )

  async def get_items_by_state(
    self,
    review_app_id: str,
    labeling_session_id: str,
    state: str,
  ) -> Dict[str, Any]:
    """Get items filtered by state.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        state: Item state to filter by (PENDING, IN_PROGRESS, COMPLETED, SKIPPED)

    Returns:
        Dictionary containing filtered items
    """
    return await self.list_items(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      filter_string=f'state={state}',
    )

  async def get_session_progress(
    self,
    review_app_id: str,
    labeling_session_id: str,
  ) -> Dict[str, Any]:
    """Get progress summary for a labeling session.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID

    Returns:
        Dictionary containing progress counts by state
    """
    all_items_response = await self.list_items(
      review_app_id=review_app_id, labeling_session_id=labeling_session_id
    )

    items = all_items_response.get('items', [])

    progress = {
      'total': len(items),
      'pending': 0,
      'in_progress': 0,
      'completed': 0,
      'skipped': 0,
    }

    for item in items:
      state = item.get('state', '').lower()
      if state == 'pending':
        progress['pending'] += 1
      elif state == 'in_progress':
        progress['in_progress'] += 1
      elif state == 'completed':
        progress['completed'] += 1
      elif state == 'skipped':
        progress['skipped'] += 1

    # Calculate completion percentage
    if progress['total'] > 0:
      progress['completion_percentage'] = round(
        (progress['completed'] + progress['skipped']) / progress['total'] * 100, 1
      )
    else:
      progress['completion_percentage'] = 0.0

    return progress

  async def delete_item(
    self,
    review_app_id: str,
    labeling_session_id: str,
    item_id: str,
  ) -> Dict[str, Any]:
    """Delete/unlink an item from the labeling session.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        item_id: The item ID to unlink

    Returns:
        Dictionary containing deletion result
    """
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}'
    )
    response = await fetch_databricks(
      method='DELETE',
      url=url,
    )

    # Handle empty response (successful deletion typically returns empty)
    if not response:
      return {'success': True, 'message': 'Item unlinked successfully'}

    return response

  async def batch_create_items(
    self,
    review_app_id: str,
    labeling_session_id: str,
    items_data: Dict[str, Any],
  ) -> Dict[str, Any]:
    """Batch create items in a labeling session.

    Args:
        review_app_id: The review app ID
        labeling_session_id: The labeling session ID
        items_data: Items data in format: {"items": [{"source": {"trace_id": "..."}}]}

    Returns:
        Dictionary containing creation result
    """
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items:batchCreate'
    )
    response = await fetch_databricks(
      method='POST',
      url=url,
      data=items_data,
    )

    return response


# Create a global instance for easy access
labeling_items_utils = LabelingItemsUtils()
