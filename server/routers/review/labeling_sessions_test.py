"""Tests for labeling sessions router.

This module tests the labeling sessions endpoints including list, get,
create, update, and delete operations.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.exceptions import NotFoundError


@pytest.fixture
def client():
  """Create test client."""
  return TestClient(app)


@pytest.fixture
def mock_labeling_sessions_utils():
  """Mock labeling sessions utility functions."""
  with patch('server.routers.review.labeling_sessions.labeling_sessions_utils') as mock:
    yield mock


class TestLabelingSessionsRouter:
  """Test labeling sessions endpoints."""

  def test_list_labeling_sessions_success(self, client, mock_labeling_sessions_utils):
    """Test successful listing of labeling sessions."""
    sessions_data = {
      'labeling_sessions': [
        {
          'labeling_session_id': 'session-123',
          'review_app_id': 'app-123',
          'name': 'Week 1 Review',
          'mlflow_run_id': 'run-123',
          'assigned_users': ['user1@example.com', 'user2@example.com'],
          'create_time': '2024-01-01T00:00:00Z',
          'created_by': 'admin@example.com',
        }
      ]
    }

    mock_labeling_sessions_utils.list_labeling_sessions.return_value = sessions_data

    response = client.get('/api/review-apps/app-123/labeling-sessions/')

    assert response.status_code == 200
    data = response.json()
    assert 'labeling_sessions' in data
    assert len(data['labeling_sessions']) == 1
    assert data['labeling_sessions'][0]['name'] == 'Week 1 Review'
    mock_labeling_sessions_utils.list_labeling_sessions.assert_called_once_with(
      'app-123', filter=None, page_size=100, page_token=None
    )

  def test_list_labeling_sessions_with_pagination(self, client, mock_labeling_sessions_utils):
    """Test listing sessions with pagination."""
    mock_labeling_sessions_utils.list_labeling_sessions.return_value = {'labeling_sessions': []}

    response = client.get(
      '/api/review-apps/app-123/labeling-sessions/?page_size=50&page_token=abc123'
    )

    assert response.status_code == 200
    mock_labeling_sessions_utils.list_labeling_sessions.assert_called_once_with(
      'app-123', filter=None, page_size=50, page_token='abc123'
    )

  def test_get_labeling_session_success(self, client, mock_labeling_sessions_utils):
    """Test getting a specific labeling session."""
    session_data = {
      'labeling_session_id': 'session-123',
      'review_app_id': 'app-123',
      'name': 'Week 1 Review',
      'mlflow_run_id': 'run-123',
      'assigned_users': ['user1@example.com'],
      'labeling_schemas': [{'name': 'quality'}],
    }

    mock_labeling_sessions_utils.get_labeling_session.return_value = session_data

    response = client.get('/api/review-apps/app-123/labeling-sessions/session-123')

    assert response.status_code == 200
    data = response.json()
    assert data['labeling_session_id'] == 'session-123'
    assert data['name'] == 'Week 1 Review'
    mock_labeling_sessions_utils.get_labeling_session.assert_called_once_with(
      'app-123', 'session-123'
    )

  def test_get_labeling_session_not_found(self, client, mock_labeling_sessions_utils):
    """Test getting non-existent labeling session."""
    mock_labeling_sessions_utils.get_labeling_session.side_effect = NotFoundError(
      'Labeling Session', 'session-999'
    )

    response = client.get('/api/review-apps/app-123/labeling-sessions/session-999')

    assert response.status_code == 404
    data = response.json()
    assert data['error']['code'] == 'RESOURCE_NOT_FOUND'

  def test_create_labeling_session_success(self, client, mock_labeling_sessions_utils):
    """Test creating a new labeling session."""
    create_data = {
      'name': 'Week 2 Review',
      'assigned_users': ['user3@example.com'],
      'labeling_schemas': [{'name': 'quality'}],
    }

    created_session = {
      'labeling_session_id': 'session-new',
      'review_app_id': 'app-123',
      'mlflow_run_id': 'run-new',
      **create_data,
    }

    mock_labeling_sessions_utils.create_labeling_session.return_value = created_session

    response = client.post('/api/review-apps/app-123/labeling-sessions/', json=create_data)

    assert response.status_code == 200
    data = response.json()
    assert data['labeling_session_id'] == 'session-new'
    assert data['name'] == 'Week 2 Review'
    mock_labeling_sessions_utils.create_labeling_session.assert_called_once_with(
      'app-123', create_data
    )

  def test_create_labeling_session_validation_error(self, client):
    """Test creating session with invalid data."""
    # Missing required field
    create_data = {'assigned_users': ['user@example.com']}

    response = client.post('/api/review-apps/app-123/labeling-sessions/', json=create_data)

    assert response.status_code == 422  # Validation error

  def test_update_labeling_session_success(self, client, mock_labeling_sessions_utils):
    """Test updating a labeling session."""
    update_data = {
      'name': 'Updated Week 1 Review',
      'assigned_users': ['user1@example.com', 'user3@example.com'],
    }

    updated_session = {
      'labeling_session_id': 'session-123',
      'review_app_id': 'app-123',
      **update_data,
    }

    mock_labeling_sessions_utils.update_labeling_session.return_value = updated_session

    response = client.patch(
      '/api/review-apps/app-123/labeling-sessions/session-123?update_mask=name,assigned_users',
      json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'Updated Week 1 Review'
    assert len(data['assigned_users']) == 2
    mock_labeling_sessions_utils.update_labeling_session.assert_called_once_with(
      'app-123', 'session-123', update_data, 'name,assigned_users'
    )

  def test_update_labeling_session_missing_mask(self, client):
    """Test updating session without update_mask."""
    update_data = {'name': 'New Name'}

    response = client.patch(
      '/api/review-apps/app-123/labeling-sessions/session-123', json=update_data
    )

    assert response.status_code == 422  # Validation error for missing update_mask

  def test_delete_labeling_session_success(self, client, mock_labeling_sessions_utils):
    """Test deleting a labeling session."""
    mock_labeling_sessions_utils.delete_labeling_session.return_value = None

    response = client.delete('/api/review-apps/app-123/labeling-sessions/session-123')

    assert response.status_code == 204  # No content
    mock_labeling_sessions_utils.delete_labeling_session.assert_called_once_with(
      'app-123', 'session-123'
    )

  def test_delete_labeling_session_not_found(self, client, mock_labeling_sessions_utils):
    """Test deleting non-existent session."""
    mock_labeling_sessions_utils.delete_labeling_session.side_effect = NotFoundError(
      'Labeling Session', 'session-999'
    )

    response = client.delete('/api/review-apps/app-123/labeling-sessions/session-999')

    assert response.status_code == 404
    data = response.json()
    assert data['error']['code'] == 'RESOURCE_NOT_FOUND'
