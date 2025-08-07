"""Tests for review apps router.

This module tests the review apps endpoints including list, get, create,
and update operations.
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
def mock_review_apps_utils():
  """Mock review apps utility functions."""
  with patch('server.routers.review.review_apps.review_apps_utils') as mock:
    yield mock


class TestReviewAppsRouter:
  """Test review apps endpoints."""

  def test_list_review_apps_success(self, client, mock_review_apps_utils):
    """Test successful listing of review apps."""
    # Mock response
    mock_review_apps_utils.list_review_apps.return_value = {
      'review_apps': [
        {
          'review_app_id': 'app-123',
          'experiment_id': 'exp-123',
          'name': 'Test Review App',
          'labeling_schemas': [],
        }
      ]
    }

    response = client.get('/api/review-apps/')

    assert response.status_code == 200
    data = response.json()
    assert 'review_apps' in data
    assert len(data['review_apps']) == 1
    assert data['review_apps'][0]['review_app_id'] == 'app-123'
    mock_review_apps_utils.list_review_apps.assert_called_once_with(filter=None)

  def test_list_review_apps_with_filter(self, client, mock_review_apps_utils):
    """Test listing review apps with filter."""
    mock_review_apps_utils.list_review_apps.return_value = {'review_apps': []}

    response = client.get('/api/review-apps/?filter=experiment_id=123')

    assert response.status_code == 200
    mock_review_apps_utils.list_review_apps.assert_called_once_with(filter='experiment_id=123')

  def test_get_review_app_success(self, client, mock_review_apps_utils):
    """Test getting a specific review app."""
    review_app_data = {
      'review_app_id': 'app-123',
      'experiment_id': 'exp-123',
      'name': 'Test Review App',
      'labeling_schemas': [
        {
          'name': 'quality',
          'title': 'Quality Rating',
          'type': 'FEEDBACK',
          'numeric': {'min_value': 1, 'max_value': 5},
        }
      ],
    }

    mock_review_apps_utils.get_review_app.return_value = review_app_data

    response = client.get('/api/review-apps/app-123')

    assert response.status_code == 200
    data = response.json()
    assert data['review_app_id'] == 'app-123'
    assert len(data['labeling_schemas']) == 1
    mock_review_apps_utils.get_review_app.assert_called_once_with('app-123')

  def test_get_review_app_not_found(self, client, mock_review_apps_utils):
    """Test getting non-existent review app."""
    mock_review_apps_utils.get_review_app.side_effect = NotFoundError('Review App', 'app-999')

    response = client.get('/api/review-apps/app-999')

    assert response.status_code == 404
    data = response.json()
    assert data['error']['code'] == 'RESOURCE_NOT_FOUND'

  def test_create_review_app_success(self, client, mock_review_apps_utils):
    """Test creating a new review app."""
    create_data = {
      'experiment_id': 'exp-123',
      'labeling_schemas': [
        {
          'name': 'quality',
          'title': 'Quality Rating',
          'type': 'FEEDBACK',
          'instruction': 'Rate the quality',
          'numeric': {'min_value': 1, 'max_value': 5},
        }
      ],
    }

    created_app = {'review_app_id': 'app-new', **create_data}

    mock_review_apps_utils.create_review_app.return_value = created_app

    response = client.post('/api/review-apps/', json=create_data)

    assert response.status_code == 200
    data = response.json()
    assert data['review_app_id'] == 'app-new'
    assert data['experiment_id'] == 'exp-123'
    mock_review_apps_utils.create_review_app.assert_called_once()

  def test_create_review_app_validation_error(self, client):
    """Test creating review app with invalid data."""
    # Missing required field
    create_data = {'labeling_schemas': []}

    response = client.post('/api/review-apps/', json=create_data)

    assert response.status_code == 422  # Validation error

  def test_update_review_app_success(self, client, mock_review_apps_utils):
    """Test updating a review app."""
    update_data = {
      'labeling_schemas': [
        {
          'name': 'quality',
          'title': 'Updated Quality Rating',
          'type': 'FEEDBACK',
          'numeric': {'min_value': 1, 'max_value': 10},
        }
      ]
    }

    updated_app = {'review_app_id': 'app-123', 'experiment_id': 'exp-123', **update_data}

    mock_review_apps_utils.update_review_app.return_value = updated_app

    response = client.patch(
      '/api/review-apps/app-123?update_mask=labeling_schemas', json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data['labeling_schemas'][0]['title'] == 'Updated Quality Rating'
    mock_review_apps_utils.update_review_app.assert_called_once_with(
      'app-123', update_data, 'labeling_schemas'
    )

  def test_update_review_app_missing_mask(self, client):
    """Test updating review app without update_mask."""
    update_data = {'labeling_schemas': []}

    response = client.patch('/api/review-apps/app-123', json=update_data)

    assert response.status_code == 422  # Validation error for missing update_mask
