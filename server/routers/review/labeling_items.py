"""Labeling Session Items endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from server.models.review_apps import (
  Item,
  ListItemsResponse,
)
from server.utils.labeling_items_utils import labeling_items_utils
from server.utils.mlflow_utils import search_traces

router = APIRouter(
  prefix='/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items',
  tags=['Labeling Items'],
)


@router.get('', response_model=ListItemsResponse)
async def list_items(
  review_app_id: str,
  labeling_session_id: str,
  filter: Optional[str] = Query(None, description='Filter string (e.g., state=PENDING)'),
  page_size: int = Query(500, ge=1, le=1000),
  page_token: Optional[str] = Query(None),
) -> Dict[str, Any]:
  """List items in a labeling session.

  Common filters:
  - state=PENDING
  - state=IN_PROGRESS
  - state=COMPLETED
  """
  # Get items from Databricks API
  response = await labeling_items_utils.list_items(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    filter_string=filter,
    page_size=page_size,
    page_token=page_token,
  )

  # Enrich items with trace preview data
  items = response.get('items', [])
  if items:
    # Collect all trace IDs
    trace_ids = []
    for item in items:
      if item.get('source', {}).get('trace_id'):
        trace_ids.append(item['source']['trace_id'])

    # Fetch trace data for all trace IDs
    if trace_ids:
      # Get experiment ID from the review app
      from server.utils.review_apps_utils import review_apps_utils

      review_app = await review_apps_utils.get_review_app(review_app_id)
      review_app.get('experiment_id')

      # Build trace ID to preview mapping
      trace_previews = {}

      # Try to find traces by searching with run_id filter
      # Get the mlflow_run_id from the labeling session
      from server.utils.labeling_sessions_utils import get_labeling_session

      session = await get_labeling_session(
        review_app_id=review_app_id, labeling_session_id=labeling_session_id
      )
      mlflow_run_id = session.get('mlflow_run_id')

      # 🚀 SIMPLE FIX: Use search_traces with run_id filter - already has previews!
      if mlflow_run_id:
        try:
          # Single search call gets ALL traces linked to this labeling session
          # with request/response previews already included - no N+1 problem!
          raw_traces = search_traces(
            experiment_ids=None,  # Will be inferred from run_id
            run_id=mlflow_run_id,
            max_results=page_size,  # Match the requested page size
          )

          # Convert raw traces to API format with assessments
          from server.routers.mlflow.mlflow import _convert_traces_to_api_format

          search_result = _convert_traces_to_api_format(raw_traces, include_spans=False)

          # Build trace_id -> preview mapping from search results
          for trace_data in search_result.get('traces', []):
            trace_id = trace_data.get('info', {}).get('trace_id')
            if trace_id in trace_ids:
              trace_previews[trace_id] = {
                'request_preview': trace_data.get('info', {}).get('request_preview'),
                'response_preview': trace_data.get('info', {}).get('response_preview'),
                'assessments': trace_data.get('info', {}).get('assessments', []),
              }

          import logging

          logger = logging.getLogger(__name__)
          logger.info(
            f'✅ Found previews for {len(trace_previews)}/{len(trace_ids)} traces '
            f'using run_id search'
          )

        except Exception as e:
          import logging

          logger = logging.getLogger(__name__)
          logger.warning(f'Failed to search traces by run_id {mlflow_run_id}: {str(e)}')

      # Add preview data and assessments to items
      for item in items:
        trace_id = item.get('source', {}).get('trace_id')
        if trace_id and trace_id in trace_previews:
          item['request_preview'] = trace_previews[trace_id].get('request_preview')
          item['response_preview'] = trace_previews[trace_id].get('response_preview')

          # Convert assessments to labels format for the UI (LabelValue format)
          # IMPORTANT: We populate labels from MLflow assessments which have correct boolean values
          # However, existing labels from Databricks API may have 1/0 instead of true/false
          assessments = trace_previews[trace_id].get('assessments', [])
          labels = {}
          for assessment in assessments:
            if assessment.get('name') and assessment.get('value') is not None:
              labels[assessment['name']] = {
                'value': assessment['value'],  # This will have the correct boolean from MLflow
                'comment': assessment.get('metadata', {}).get('comment')
                if isinstance(assessment.get('metadata'), dict)
                else None,
              }
          
          # Only override labels if we have assessment data
          # Otherwise keep the existing labels from Databricks API
          if labels:
            item['labels'] = labels

  return response


@router.post('/batchCreate')
async def batch_create_items(
  review_app_id: str,
  labeling_session_id: str,
  request: Dict[str, Any],
) -> Dict[str, Any]:
  """Batch create items by proxying to Databricks API."""
  return await labeling_items_utils.batch_create_items(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    items_data=request,
  )


@router.get('/{item_id}', response_model=Item)
async def get_item(
  review_app_id: str,
  labeling_session_id: str,
  item_id: str,
) -> Dict[str, Any]:
  """Get a specific item."""
  return await labeling_items_utils.get_item(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    item_id=item_id,
  )


@router.patch('/{item_id}', response_model=Item)
async def update_item(
  review_app_id: str,
  labeling_session_id: str,
  item_id: str,
  item: Item,
  update_mask: str = Query(..., description='Comma-separated list of fields to update'),
) -> Dict[str, Any]:
  """Update an item.

  Example update_mask: "state,chat_rounds"
  """
  import logging

  logger = logging.getLogger(__name__)

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
  review_app_id: str,
  labeling_session_id: str,
  item_id: str,
) -> Dict[str, Any]:
  """Delete/unlink an item from the labeling session."""
  return await labeling_items_utils.delete_item(
    review_app_id=review_app_id,
    labeling_session_id=labeling_session_id,
    item_id=item_id,
  )
