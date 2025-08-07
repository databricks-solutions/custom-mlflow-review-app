"""Pytest configuration and fixtures for server tests.

This module provides common fixtures and configuration for all server tests.
"""

import os
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_environment():
  """Mock environment variables for all tests."""
  env_vars = {
    'DATABRICKS_HOST': 'https://test.databricks.com',
    'DATABRICKS_CLIENT_ID': 'test-client-id',
    'DATABRICKS_CLIENT_SECRET': 'test-client-secret',
    'DATABRICKS_WORKSPACE_ID': 'test-workspace-id',
    'EXPERIMENT_ID': 'test-experiment-123',
    'SQL_WAREHOUSE_ID': 'test-warehouse-456',
  }

  with patch.dict(os.environ, env_vars):
    yield


@pytest.fixture
def mock_httpx_client():
  """Mock httpx client for external API calls."""
  with patch('httpx.AsyncClient') as mock_client_class:
    mock_client = Mock()
    mock_client_class.return_value = mock_client

    # Default successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    mock_response.text = '{"status": "success"}'
    mock_response.headers = {'content-type': 'application/json'}

    mock_client.request.return_value = mock_response
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.patch.return_value = mock_response
    mock_client.delete.return_value = mock_response

    yield mock_client


@pytest.fixture
def test_review_app():
  """Sample review app data for tests."""
  return {
    'review_app_id': 'app-test-123',
    'experiment_id': 'test-experiment-123',
    'labeling_schemas': [
      {
        'name': 'quality',
        'title': 'Quality Rating',
        'type': 'FEEDBACK',
        'instruction': 'Rate the quality of the response',
        'numeric': {'min_value': 1, 'max_value': 5},
      },
      {
        'name': 'helpfulness',
        'title': 'Helpfulness',
        'type': 'FEEDBACK',
        'categorical': {'options': ['Very Helpful', 'Somewhat Helpful', 'Not Helpful']},
      },
    ],
  }


@pytest.fixture
def test_labeling_session():
  """Sample labeling session data for tests."""
  return {
    'labeling_session_id': 'session-test-123',
    'review_app_id': 'app-test-123',
    'name': 'Test Session',
    'mlflow_run_id': 'run-test-123',
    'assigned_users': ['user1@example.com', 'user2@example.com'],
    'labeling_schemas': [{'name': 'quality'}, {'name': 'helpfulness'}],
    'create_time': '2024-01-01T00:00:00Z',
    'created_by': 'admin@example.com',
  }


@pytest.fixture
def test_trace():
  """Sample trace data for tests."""
  return {
    'trace_id': 'tr-test-123',
    'trace_info': {
      'experiment_id': 'test-experiment-123',
      'status': 'OK',
      'timestamp_ms': 1704067200000,  # 2024-01-01
      'execution_time_ms': 1500,
      'request_id': 'req-123',
    },
    'trace_data': {
      'spans': [
        {
          'name': 'main',
          'span_type': 'CHAIN',
          'start_time': 1704067200000,
          'end_time': 1704067201500,
          'status': 'OK',
          'attributes': {'chain_type': 'qa_chain'},
        },
        {
          'name': 'llm_call',
          'span_type': 'CHAT_MODEL',
          'start_time': 1704067200100,
          'end_time': 1704067201000,
          'status': 'OK',
          'attributes': {
            'model': 'gpt-4',
            'messages': [
              {'role': 'user', 'content': 'What is the capital of France?'},
              {'role': 'assistant', 'content': 'The capital of France is Paris.'},
            ],
          },
        },
      ]
    },
  }


@pytest.fixture
def test_labeling_item():
  """Sample labeling item data for tests."""
  return {
    'item_id': 'item-test-123',
    'labeling_session_id': 'session-test-123',
    'source': {'trace_id': 'tr-test-123'},
    'state': 'PENDING',
    'labels': {},
    'comment': None,
    'created_by': None,
    'create_time': '2024-01-01T00:00:00Z',
  }
