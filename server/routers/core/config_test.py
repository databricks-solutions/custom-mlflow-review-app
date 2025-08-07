"""Tests for configuration router.

This module tests the configuration endpoints including getting
app configuration and experiment ID.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture
def client():
  """Create test client."""
  return TestClient(app)


@pytest.fixture
def mock_config():
  """Mock the config object."""
  with patch('server.routers.core.config.config') as mock:
    mock.experiment_id = 'test-experiment-123'
    mock.max_results = 1000
    mock.page_size = 500
    mock.debug = False
    yield mock


class TestConfigRouter:
  """Test configuration endpoints."""

  def test_get_config_success(self, client, mock_config):
    """Test getting application configuration."""
    response = client.get('/api/config/')

    assert response.status_code == 200
    data = response.json()
    assert data['experiment_id'] == 'test-experiment-123'
    assert data['max_results'] == 1000
    assert data['page_size'] == 500
    assert data['debug'] is False

  def test_get_config_missing_experiment_id(self, client, mock_config):
    """Test config when experiment_id is not set."""
    mock_config.experiment_id = None

    response = client.get('/api/config/')

    assert response.status_code == 200
    data = response.json()
    assert data['experiment_id'] is None

  def test_get_experiment_id_success(self, client, mock_config):
    """Test getting just the experiment ID."""
    response = client.get('/api/config/experiment-id')

    assert response.status_code == 200
    data = response.json()
    assert data['experiment_id'] == 'test-experiment-123'

  def test_get_experiment_id_not_configured(self, client, mock_config):
    """Test getting experiment ID when not configured."""
    mock_config.experiment_id = None

    response = client.get('/api/config/experiment-id')

    assert response.status_code == 200
    data = response.json()
    assert data['experiment_id'] is None
