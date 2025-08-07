"""Tests for Databricks authentication utilities.

This module tests URL building, authentication header generation,
and configuration management for Databricks API integration.
"""

from unittest.mock import patch

import pytest

from server.exceptions import ConfigurationError
from server.utils.databricks_auth import (
  APIType,
  build_databricks_url,
  get_databricks_config,
  get_databricks_headers,
  get_managed_evals_api_url,
  get_mlflow_api_url,
)


class TestDatabricksAuth:
  """Test Databricks authentication utilities."""

  def test_api_type_enum(self):
    """Test APIType enum values."""
    assert APIType.MLFLOW.value == '/api/2.0/mlflow'
    assert APIType.MANAGED_EVALS.value == '/api/2.0/managed-evals'
    assert APIType.WORKSPACE.value == '/api/2.0/workspace'
    assert APIType.CLUSTERS.value == '/api/2.0/clusters'
    assert APIType.SQL_WAREHOUSES.value == '/api/2.0/sql/warehouses'
    assert APIType.SERVING_ENDPOINTS.value == '/api/2.0/serving-endpoints'
    assert APIType.JOBS.value == '/api/2.0/jobs'
    assert APIType.DBFS.value == '/api/2.0/dbfs'

  @patch('databricks.sdk.WorkspaceClient')
  def test_get_databricks_config_success(self, mock_workspace_client):
    """Test successful configuration retrieval."""
    # Mock the WorkspaceClient and its methods
    mock_client = mock_workspace_client.return_value
    mock_client.config.host = 'https://test.databricks.com/'
    mock_client.config.token = 'test-token'
    mock_client.current_user.me.return_value.user_name = 'test@example.com'

    config = get_databricks_config()

    assert config['host'] == 'https://test.databricks.com'  # Trailing slash removed
    assert config['token'] == 'test-token'
    assert config['username'] == 'test@example.com'

  def test_get_databricks_config_auth_error(self):
    """Test configuration error when authentication fails."""
    # Clear the cache first
    get_databricks_config.cache_clear()

    with patch('databricks.sdk.WorkspaceClient') as mock_workspace_client:
      # Mock WorkspaceClient to raise an exception
      mock_workspace_client.side_effect = Exception('Authentication failed')

      with pytest.raises(ConfigurationError) as exc_info:
        get_databricks_config()

      assert 'Unable to authenticate with Databricks' in str(exc_info.value)

  @patch('databricks.sdk.WorkspaceClient')
  def test_get_databricks_headers_basic(self, mock_workspace_client):
    """Test basic authentication headers."""
    mock_client = mock_workspace_client.return_value
    mock_client.config.token = 'test-token'

    headers = get_databricks_headers()

    assert headers['Authorization'] == 'Bearer test-token'
    assert headers['Content-Type'] == 'application/json'
    assert 'X-Databricks-CSRF-Token' not in headers

  @patch('databricks.sdk.WorkspaceClient')
  def test_build_databricks_url_basic(self, mock_workspace_client):
    """Test basic URL building."""
    mock_client = mock_workspace_client.return_value
    mock_client.config.host = 'https://test.databricks.com'
    mock_client.config.token = 'test-token'
    mock_client.current_user.me.return_value.user_name = 'test@example.com'

    url = build_databricks_url(APIType.MLFLOW, '/experiments/get')

    assert url == 'https://test.databricks.com/api/2.0/mlflow/experiments/get'

  @patch('databricks.sdk.WorkspaceClient')
  def test_convenience_functions(self, mock_workspace_client):
    """Test convenience functions for specific API types."""
    mock_client = mock_workspace_client.return_value
    mock_client.config.host = 'https://test.databricks.com'
    mock_client.config.token = 'test-token'
    mock_client.current_user.me.return_value.user_name = 'test@example.com'

    # Test MLflow URL
    mlflow_url = get_mlflow_api_url('/experiments/get')
    assert mlflow_url == 'https://test.databricks.com/api/2.0/mlflow/experiments/get'

    # Test Managed Evals URL
    evals_url = get_managed_evals_api_url('/review-apps/list')
    assert evals_url == 'https://test.databricks.com/api/2.0/managed-evals/review-apps/list'
