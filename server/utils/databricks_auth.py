"""Databricks authentication and URL building utilities.

This module provides utilities for:
- Loading Databricks configuration from environment variables
- Building properly formatted URLs for different Databricks API types
- Generating authentication headers for API requests
"""

from enum import Enum
from functools import lru_cache
from typing import Dict

from server.exceptions import ConfigurationError


class APIType(Enum):
  """Databricks API types with their base paths."""

  MLFLOW = '/api/2.0/mlflow'
  MANAGED_EVALS = '/api/2.0/managed-evals'
  WORKSPACE = '/api/2.0/workspace'
  CLUSTERS = '/api/2.0/clusters'
  SQL_WAREHOUSES = '/api/2.0/sql/warehouses'
  SERVING_ENDPOINTS = '/api/2.0/serving-endpoints'
  JOBS = '/api/2.0/jobs'
  DBFS = '/api/2.0/dbfs'


@lru_cache(maxsize=1)
def get_databricks_config() -> Dict[str, str]:
  """Get Databricks configuration using WorkspaceClient authentication."""
  from databricks.sdk import WorkspaceClient

  try:
    # WorkspaceClient automatically handles authentication from env vars
    # Supports both DATABRICKS_TOKEN (local) and OAuth (Databricks Apps)
    client = WorkspaceClient()

    # Test authentication by getting current user
    current_user = client.current_user.me()

    # Get host from client config
    host = client.config.host
    if not host:
      raise ConfigurationError(
        'DATABRICKS_HOST must be set in environment variables',
        config_key='DATABRICKS_HOST',
      )

    # Ensure host doesn't have trailing slash
    host = host.rstrip('/')

    return {
      'host': host,
      'token': client.config.token or '',  # May be empty for OAuth
      'username': current_user.user_name,
    }

  except Exception as e:
    raise ConfigurationError(
      f'Unable to authenticate with Databricks: {str(e)}',
      config_key='DATABRICKS_AUTH',
    )


def get_databricks_headers(include_csrf: bool = False) -> Dict[str, str]:
  """Get authentication headers for Databricks API calls.

  Args:
    include_csrf: Whether to include CSRF token for ajax-api endpoints
  """
  from databricks.sdk import WorkspaceClient

  client = WorkspaceClient()

  headers = {
    'Content-Type': 'application/json',
  }

  # Add authorization header if token is available
  if client.config.token:
    headers['Authorization'] = f'Bearer {client.config.token}'

    if include_csrf:
      # For ajax-api endpoints, we need to include a CSRF token
      headers['X-Databricks-CSRF-Token'] = client.config.token

  return headers


def build_databricks_url(api_type: APIType, path: str) -> str:
  """Build a Databricks API URL for the given API type and path.

  Args:
    api_type: The type of API (e.g., APIType.MLFLOW)
    path: The endpoint path (e.g., "/experiments/get")

  Returns:
    Complete URL for the API endpoint

  Examples:
    >>> build_databricks_url(APIType.MLFLOW, "/experiments/get")
    "https://workspace.databricks.com/api/2.0/mlflow/experiments/get"
  """
  config = get_databricks_config()

  # Ensure path starts with /
  if not path.startswith('/'):
    path = f'/{path}'

  # Build the complete URL
  return f'{config["host"]}{api_type.value}{path}'


# Convenience functions for specific API types
def get_mlflow_api_url(path: str) -> str:
  """Build URL for MLflow API endpoints."""
  return build_databricks_url(APIType.MLFLOW, path)


def get_managed_evals_api_url(path: str) -> str:
  """Build URL for Managed Evaluations (Review Apps) API endpoints."""
  return build_databricks_url(APIType.MANAGED_EVALS, path)


def get_workspace_api_url(path: str) -> str:
  """Build URL for Workspace API endpoints."""
  return build_databricks_url(APIType.WORKSPACE, path)


def get_serving_api_url(path: str) -> str:
  """Build URL for Model Serving API endpoints."""
  return build_databricks_url(APIType.SERVING_ENDPOINTS, path)
