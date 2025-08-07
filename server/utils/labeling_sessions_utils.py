"""Labeling Sessions utility functions for direct use as tools by Claude."""

from typing import Any, Dict, List, Optional

import mlflow
import mlflow.genai.labeling as labeling

from server.utils.databricks_auth import get_managed_evals_api_url
from server.utils.proxy import fetch_databricks


async def list_labeling_sessions(
  review_app_id: str,
  filter_string: Optional[str] = None,
  page_size: int = 500,
  page_token: Optional[str] = None,
) -> Dict[str, Any]:
  """List labeling sessions for a review app.

  Args:
      review_app_id: The review app ID
      filter_string: Filter string (e.g., state=IN_PROGRESS, assigned_users=user@example.com)
      page_size: Number of items per page (1-1000)
      page_token: Pagination token for next page

  Returns:
      Dictionary containing list of labeling sessions and pagination info
  """
  try:
    import logging
    import time

    logger = logging.getLogger(__name__)
    logger.info('🧬 [MLFLOW GENAI] Trying SDK approach for list_labeling_sessions')

    # Get all labeling sessions using SDK
    genai_start = time.time()
    all_sessions = labeling.get_labeling_sessions()
    genai_time = time.time() - genai_start
    logger.info(
      f'🧬 [MLFLOW GENAI] get_labeling_sessions() completed in {genai_time * 1000:.1f}ms, returned {len(all_sessions) if all_sessions else 0} sessions'
    )

    # Filter by review app ID and convert to dict format
    for session in all_sessions:
      # Check if session belongs to this review app
      # Note: SDK doesn't provide review_app_id directly, so we use REST API fallback
      raise Exception("SDK doesn't provide review_app_id filtering")

  except Exception as e:
    print(f'🔄 UTILS_LIST_SESSIONS: SDK failed with {str(e)}, falling back to REST API')
    # Fallback to REST API
    params = {'page_size': page_size}
    if filter_string:
      params['filter'] = filter_string
    if page_token:
      params['page_token'] = page_token

    url = get_managed_evals_api_url(f'/review-apps/{review_app_id}/labeling-sessions')
    response = await fetch_databricks(
      method='GET',
      url=url,
      params=params,
    )

    # Handle empty response
    if not response:
      return {'labeling_sessions': [], 'next_page_token': None}

    # Ensure response has the expected structure
    if 'labeling_sessions' not in response:
      response = {'labeling_sessions': [], 'next_page_token': None}

    return response


async def create_labeling_session(
  review_app_id: str,
  labeling_session_data: Dict[str, Any],
) -> Dict[str, Any]:
  """Create a new labeling session.

  Args:
      review_app_id: The review app ID
      labeling_session_data: Labeling session data (auto-generated fields will be removed)

  Returns:
      Dictionary containing created labeling session
  """
  try:
    # Get experiment ID from review app - use cached version to avoid slow API calls
    from server.config import get_config

    # Since we only have one review app per experiment, and we know the experiment_id from config,
    # we can avoid the expensive API call by getting the experiment_id directly from config
    config = get_config()
    experiment_id = config.experiment_id

    if not experiment_id:
      raise Exception(f'No experiment_id found for review app {review_app_id}')

    # Set experiment context
    mlflow.set_experiment(experiment_id=experiment_id)

    # Create labeling session using SDK
    session = labeling.create_labeling_session(
      name=labeling_session_data.get('name'),
      assigned_users=labeling_session_data.get('assigned_users', []),
      label_schemas=labeling_session_data.get('labeling_schemas', []),
      # Other fields as supported by SDK
    )

    # Convert to dictionary format
    return {
      'labeling_session_id': session.labeling_session_id,
      'name': session.name,
      'assigned_users': session.assigned_users,
      'mlflow_run_id': session.mlflow_run_id,
      'labeling_schemas': getattr(session, 'label_schemas', []),
      # Add other fields as needed
    }

  except Exception:
    # Fallback to REST API
    # Remove auto-generated fields
    data = labeling_session_data.copy()
    data.pop('labeling_session_id', None)
    data.pop('mlflow_run_id', None)
    data.pop('create_time', None)
    data.pop('created_by', None)
    data.pop('last_update_time', None)
    data.pop('last_updated_by', None)

    url = get_managed_evals_api_url(f'/review-apps/{review_app_id}/labeling-sessions')
    response = await fetch_databricks(
      method='POST',
      url=url,
      data=data,
    )

    return response


async def get_labeling_session(
  review_app_id: str,
  labeling_session_id: str,
) -> Dict[str, Any]:
  """Get a specific labeling session.

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID

  Returns:
      Dictionary containing labeling session details
  """
  try:
    # Get experiment ID from config - avoid expensive API calls since we have 1:1 mapping
    from server.config import get_config

    config = get_config()
    experiment_id = config.experiment_id

    if not experiment_id:
      raise Exception(f'No experiment_id found for review app {review_app_id}')

    # Set experiment context
    mlflow.set_experiment(experiment_id=experiment_id)

    # Get all labeling sessions to find the specific one
    all_sessions = labeling.get_labeling_sessions()

    for session in all_sessions:
      if session.labeling_session_id == labeling_session_id:
        # Convert to dictionary format
        return {
          'labeling_session_id': session.labeling_session_id,
          'name': session.name,
          'assigned_users': session.assigned_users,
          'mlflow_run_id': session.mlflow_run_id,
          'labeling_schemas': [
            {'name': schema} for schema in getattr(session, 'label_schemas', [])
          ],
          'create_time': getattr(session, 'create_time', None),
          'created_by': getattr(session, 'created_by', None),
          'last_update_time': getattr(session, 'last_update_time', None),
          'last_updated_by': getattr(session, 'last_updated_by', None),
          'agent': getattr(session, 'agent', None),
          'dataset': getattr(session, 'dataset', None),
          'additional_configs': getattr(session, 'additional_configs', None),
        }

    raise Exception(f'Labeling session {labeling_session_id} not found')

  except Exception:
    # Fallback to REST API
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}'
    )
    response = await fetch_databricks(
      method='GET',
      url=url,
    )

    return response


async def update_labeling_session(
  review_app_id: str,
  labeling_session_id: str,
  labeling_session_data: Dict[str, Any],
  update_mask: str,
) -> Dict[str, Any]:
  """Update a labeling session using the official MLflow SDK.

  The SDK automatically handles experiment permissions when updating assigned_users.

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID
      labeling_session_data: Updated labeling session data
      update_mask: Comma-separated list of fields to update (e.g., "name,assigned_users")

  Returns:
      Dictionary containing updated labeling session
  """
  # Check if we're updating assigned_users - use MLflow SDK for proper permission handling
  if 'assigned_users' in update_mask and 'assigned_users' in labeling_session_data:
    return await _update_session_with_sdk(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      labeling_session_data=labeling_session_data,
      update_mask=update_mask,
    )

  # For non-user updates, use REST API
  url = get_managed_evals_api_url(
    f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}'
  )
  params = {'update_mask': update_mask}

  response = await fetch_databricks(
    method='PATCH',
    url=url,
    data=labeling_session_data,
    params=params,
  )

  return response


async def _update_session_with_sdk(
  review_app_id: str,
  labeling_session_id: str,
  labeling_session_data: Dict[str, Any],
  update_mask: str,
) -> Dict[str, Any]:
  """Update labeling session using MLflow SDK for proper permission handling.

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID
      labeling_session_data: Updated labeling session data
      update_mask: Comma-separated list of fields to update

  Returns:
      Dictionary containing updated labeling session
  """
  import mlflow
  import mlflow.genai.labeling as labeling

  try:
    # Get experiment ID from config - avoid expensive API calls since we have 1:1 mapping
    from server.config import get_config

    config = get_config()
    experiment_id = config.experiment_id

    if not experiment_id:
      raise Exception(f'No experiment_id found for review app {review_app_id}')

    # Set experiment context for MLflow SDK
    mlflow.set_experiment(experiment_id=experiment_id)

    # Get all labeling sessions to find the one we want to update
    all_sessions = labeling.get_labeling_sessions()
    target_session = None

    for session in all_sessions:
      if session.labeling_session_id == labeling_session_id:
        target_session = session
        break

    if not target_session:
      raise Exception(f'Labeling session {labeling_session_id} not found')

    # Update assigned users using SDK (handles permissions automatically)
    if 'assigned_users' in labeling_session_data:
      target_session.set_assigned_users(labeling_session_data['assigned_users'])
      print(
        '✅ Updated assigned users using MLflow SDK (automatically handles experiment permissions)'
      )

    # For other fields, we still need to use REST API
    other_updates = {k: v for k, v in labeling_session_data.items() if k != 'assigned_users'}
    other_mask_fields = [field for field in update_mask.split(',') if field != 'assigned_users']

    if other_updates and other_mask_fields:
      url = get_managed_evals_api_url(
        f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}'
      )
      params = {'update_mask': ','.join(other_mask_fields)}

      await fetch_databricks(
        method='PATCH',
        url=url,
        data=other_updates,
        params=params,
      )

    # Return updated session data
    return await get_labeling_session(review_app_id, labeling_session_id)

  except Exception as e:
    # Fallback to REST API if SDK fails
    print(f'⚠️  Warning: SDK update failed, falling back to REST API: {str(e)}')
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}'
    )
    params = {'update_mask': update_mask}

    response = await fetch_databricks(
      method='PATCH',
      url=url,
      data=labeling_session_data,
      params=params,
    )

    return response


async def delete_labeling_session(
  review_app_id: str,
  labeling_session_id: str,
) -> Dict[str, Any]:
  """Delete a labeling session.

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID

  Returns:
      Dictionary containing success message
  """
  try:
    # Get experiment ID from config - avoid expensive API calls since we have 1:1 mapping
    from server.config import get_config

    config = get_config()
    experiment_id = config.experiment_id

    if not experiment_id:
      raise Exception(f'No experiment_id found for review app {review_app_id}')

    # Set experiment context
    mlflow.set_experiment(experiment_id=experiment_id)

    # Get all labeling sessions to find the one we want to delete
    all_sessions = labeling.get_labeling_sessions()
    target_session = None

    for session in all_sessions:
      if session.labeling_session_id == labeling_session_id:
        target_session = session
        break

    if not target_session:
      raise Exception(f'Labeling session {labeling_session_id} not found')

    # Delete labeling session using SDK
    labeling.delete_labeling_session(target_session)

    return {'message': 'Labeling session deleted successfully'}

  except Exception:
    # Fallback to REST API
    url = get_managed_evals_api_url(
      f'/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}'
    )
    await fetch_databricks(
      method='DELETE',
      url=url,
    )

    return {'message': 'Labeling session deleted successfully'}


async def get_session_by_name(
  review_app_id: str,
  session_name: str,
) -> Optional[Dict[str, Any]]:
  """Get labeling session by name.

  Args:
      review_app_id: The review app ID
      session_name: The session name to search for

  Returns:
      Dictionary containing labeling session details, or None if not found
  """
  try:
    response = await list_labeling_sessions(
      review_app_id=review_app_id, filter_string=f'name={session_name}'
    )
    sessions = response.get('labeling_sessions', [])

    if sessions:
      return sessions[0]  # Return the first (should be only) match
    return None
  except Exception:
    return None


async def link_traces_to_session(
  review_app_id: str,
  labeling_session_id: str,
  mlflow_run_id: str,
  trace_ids: List[str],
) -> Dict[str, Any]:
  """Link traces to an MLflow run and add them as items to a labeling session.

  This combines two operations:
  1. Link traces to the MLflow run (via MLflow API)
  2. Create labeling items for the traces in the session (via Managed Evals API)

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID
      mlflow_run_id: The MLflow run ID to link traces to
      trace_ids: List of trace IDs to link and add

  Returns:
      Dictionary containing results from both operations
  """
  from server.utils.labeling_items_utils import labeling_items_utils
  from server.utils.mlflow_utils import link_traces_to_run

  try:
    # Step 1: Link traces to MLflow run
    link_result = link_traces_to_run(run_id=mlflow_run_id, trace_ids=trace_ids)

    # Step 2: Create labeling items for the traces
    items_data = {'items': [{'source': {'trace_id': trace_id}} for trace_id in trace_ids]}

    create_result = await labeling_items_utils.batch_create_items(
      review_app_id=review_app_id,
      labeling_session_id=labeling_session_id,
      items_data=items_data,
    )

    return {
      'success': True,
      'linked_traces': len(trace_ids),
      'mlflow_link_result': link_result,
      'labeling_items_result': create_result,
    }

  except Exception as e:
    return {
      'success': False,
      'error': str(e),
      'trace_ids_attempted': trace_ids,
    }
