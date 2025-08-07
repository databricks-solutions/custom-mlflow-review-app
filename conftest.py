"""Pytest configuration and fixtures for MLflow Review App tests.

This module provides shared fixtures and configuration for all tests,
including mock setups, test data, and utility functions.
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables
os.environ['DATABRICKS_HOST'] = 'https://test.databricks.com'
os.environ['DATABRICKS_TOKEN'] = 'test-token'


@pytest.fixture
def test_client():
  """Create a test client for the FastAPI application."""
  from server.app import app

  with TestClient(app) as client:
    yield client


@pytest.fixture
def mock_databricks_config():
  """Mock Databricks configuration."""
  config = {'host': 'https://test.databricks.com', 'token': 'test-token'}

  with patch('server.utils.databricks_auth.get_databricks_config', return_value=config):
    yield config


@pytest.fixture
def sample_trace():
  """Sample trace data for testing."""
  return {
    'info': {
      'trace_id': 'tr-12345',
      'request_time': '2024-01-01T00:00:00Z',
      'execution_duration': '1500ms',
      'state': 'FINISHED',
      'trace_location': {'experiment_id': '2178582188830602', 'run_id': 'run-67890'},
      'tags': {'user': 'test@example.com', 'environment': 'test'},
    },
    'data': {
      'spans': [
        {
          'name': 'chat_completion',
          'span_id': 'span-1',
          'span_type': 'CHAT_MODEL',
          'start_time_ms': 1640995200000,
          'end_time_ms': 1640995201000,
          'attributes': {'mlflow.spanType': 'CHAT_MODEL'},
        }
      ]
    },
  }


@pytest.fixture
def sample_review_app():
  """Sample review app data for testing."""
  return {
    'review_app_id': 'review-app-123',
    'experiment_id': '2178582188830602',
    'agents': [
      {
        'agent_name': 'test-agent',
        'model_serving_endpoint': {
          'endpoint_name': 'test-endpoint',
          'served_entity_name': 'test-model',
        },
      }
    ],
    'labeling_schemas': [
      {
        'name': 'quality',
        'type': 'FEEDBACK',
        'title': 'Quality Rating',
        'instruction': 'Rate the quality of the response',
        'numeric': {'min_value': 1, 'max_value': 5},
      }
    ],
  }
