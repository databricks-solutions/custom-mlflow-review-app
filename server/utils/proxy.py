"""HTTP client utilities for Databricks API calls."""

import inspect
import json
import logging
import time
from functools import lru_cache
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from fastapi import HTTPException
from mlflow.utils.databricks_utils import get_databricks_host_creds
from mlflow.utils.rest_utils import http_request_safe

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lru_cache(maxsize=1)
def get_cached_databricks_creds():
  """Get Databricks credentials with caching.

  This caches the credentials for the lifetime of the process,
  avoiding repeated lookups of environment variables and config files.

  Returns:
      Databricks host credentials object
  """
  logger.info('🔐 [DATABRICKS] Loading credentials (this should only happen once)')
  return get_databricks_host_creds()


def fetch_databricks_sync(
  method: str,
  url: str,
  data: Optional[Union[Dict[str, Any], Any]] = None,
  params: Optional[Dict[str, Any]] = None,
  timeout: float = 30.0,
) -> Any:
  """Synchronous HTTP client for Databricks API calls using MLflow utilities.

  Args:
      method: HTTP method (GET, POST, PATCH, DELETE)
      url: Full URL to call
      data: Request body data
      params: Query parameters
      timeout: Request timeout in seconds

  Returns:
      Response data (JSON decoded)

  Raises:
      HTTPException: If the request fails
  """
  logger = logging.getLogger(__name__)
  start_time = time.time()

  # Extract endpoint path for logging
  parsed_url = urlparse(url)
  endpoint_path = parsed_url.path
  endpoint_name = '/'.join(endpoint_path.split('/')[-2:]) if '/' in endpoint_path else endpoint_path

  # Get caller information for better tracing
  frame = inspect.currentframe()
  caller_info = 'unknown'
  if frame and frame.f_back and frame.f_back.f_back:
    caller_frame = frame.f_back.f_back
    caller_module = caller_frame.f_globals.get('__name__', 'unknown')
    caller_function = caller_frame.f_code.co_name
    caller_line = caller_frame.f_lineno
    caller_info = f'{caller_module}:{caller_function}:{caller_line}'

  logger.info(f'🌐 [DATABRICKS] {method} {endpoint_name} | Called from: {caller_info}')
  if data:
    logger.info(f'📤 [DATABRICKS] Request payload size: {len(str(data))} chars')
  if params:
    logger.info(f'🔍 [DATABRICKS] Query params: {params}')

  try:
    # Get Databricks credentials (cached)
    creds_start = time.time()
    creds = get_cached_databricks_creds()
    creds_time = time.time() - creds_start
    if creds_time > 0.001:  # Only log if it took more than 1ms (i.e., not cached)
      logger.info(f'🔐 [DATABRICKS] Credentials lookup: {creds_time * 1000:.1f}ms (fresh load)')
    else:
      logger.debug(f'🔐 [DATABRICKS] Credentials lookup: {creds_time * 1000:.1f}ms (cached)')

    # Build endpoint with params
    endpoint = parsed_url.path
    if parsed_url.query:
      endpoint += f'?{parsed_url.query}'
    if params:
      separator = '&' if parsed_url.query else '?'
      param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
      endpoint += f'{separator}{param_str}'

    # Make request
    request_start = time.time()
    response = http_request_safe(
      method=method.upper(),
      endpoint=endpoint,
      host_creds=creds,
      json=data if data is not None else None,
      timeout=timeout,
    )

    request_time = time.time() - request_start
    total_time = time.time() - start_time
    logger.info(
      f'✅ [DATABRICKS] {method} {endpoint_name} completed in {total_time * 1000:.1f}ms '
      f'(creds: {creds_time * 1000:.1f}ms, request: {request_time * 1000:.1f}ms)'
    )

    # Parse response
    try:
      return response.json()
    except (json.JSONDecodeError, ValueError):
      # Return empty dict for empty responses or text for non-JSON
      return {} if response.status_code == 204 or not response.text else response.text

  except Exception as e:
    error_time = time.time() - start_time
    logger.error(
      f'❌ [DATABRICKS] {method} {endpoint_name} error after {error_time * 1000:.1f}ms: {str(e)}'
    )

    # Extract error details
    status_code = getattr(getattr(e, 'response', None), 'status_code', 500)
    if hasattr(e, 'response'):
      try:
        error_detail = e.response.json() if hasattr(e.response, 'json') else str(e)
      except:
        error_detail = str(e)
    else:
      error_detail = f'Request failed: {str(e)}'

    raise HTTPException(
      status_code=status_code,
      detail=f'Databricks API error: {error_detail}',
    ) from e


async def fetch_databricks(
  method: str,
  url: str,
  data: Optional[Union[Dict[str, Any], Any]] = None,
  params: Optional[Dict[str, Any]] = None,
  timeout: float = 30.0,
) -> Any:
  """Async wrapper for Databricks API calls.

  Note: Since MLflow utilities are synchronous, this just calls the sync version.
  Kept for backwards compatibility with async endpoints.
  """
  return fetch_databricks_sync(method, url, data, params, timeout)
