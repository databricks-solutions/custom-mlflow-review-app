"""Tests for MLflow router.

This module tests the MLflow proxy endpoints including experiments,
runs, and traces operations.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.exceptions import MLflowError


@pytest.fixture
def client():
  """Create test client."""
  return TestClient(app)


@pytest.fixture
def mock_mlflow_functions():
  """Mock MLflow utility functions."""
  with (
    patch('server.routers.mlflow.mlflow.search_traces') as mock_search_traces,
    patch('server.routers.mlflow.mlflow.get_experiment') as mock_get_experiment,
    patch('server.routers.mlflow.mlflow.get_run') as mock_get_run,
    patch('server.routers.mlflow.mlflow.create_run') as mock_create_run,
    patch('server.routers.mlflow.mlflow.update_run') as mock_update_run,
    patch('server.routers.mlflow.mlflow.search_runs') as mock_search_runs,
    patch('server.routers.mlflow.mlflow.link_traces_to_run') as mock_link_traces_to_run,
    patch('server.routers.mlflow.mlflow.get_trace') as mock_get_trace,
    patch('server.routers.mlflow.mlflow.get_trace_data') as mock_get_trace_data,
  ):
    # Create a mock object that has all the methods for backward compatibility with tests
    class MockMLflowUtils:
      def __init__(self):
        self.search_traces = mock_search_traces
        self.get_experiment = mock_get_experiment
        self.get_run = mock_get_run
        self.create_run = mock_create_run
        self.update_run = mock_update_run
        self.search_runs = mock_search_runs
        self.link_traces_to_run = mock_link_traces_to_run
        self.get_trace = mock_get_trace
        self.get_trace_data = mock_get_trace_data

    yield MockMLflowUtils()


class TestMLflowRouter:
  """Test MLflow endpoints."""

  def test_get_experiment_success(self, client, mock_mlflow_functions):
    """Test getting experiment details."""
    experiment_data = {
      'experiment': {
        'experiment_id': '123',
        'name': 'Test Experiment',
        'artifact_location': 'dbfs:/experiments/123',
        'lifecycle_stage': 'active',
        'creation_time': 1704067200000,
        'last_update_time': 1704067200000,
      }
    }

    # Create a regular mock since the utils method is synchronous
    mock_mlflow_functions.get_experiment.return_value = experiment_data

    response = client.get('/api/mlflow/experiments/123')

    assert response.status_code == 200
    data = response.json()
    assert data['experiment']['experiment_id'] == '123'
    assert data['experiment']['name'] == 'Test Experiment'
    mock_mlflow_functions.get_experiment.assert_called_once_with('123')

  def test_get_experiment_not_found(self, client, mock_mlflow_functions):
    """Test getting non-existent experiment."""
    mock_mlflow_functions.get_experiment.side_effect = MLflowError(
      'Experiment not found', 'get_experiment'
    )

    response = client.get('/api/mlflow/experiments/999')

    assert response.status_code == 500
    data = response.json()
    assert 'MLflow operation failed' in data['error']['message']

  def test_search_traces_success(self, client, mock_mlflow_functions):
    """Test searching traces."""
    search_request = {'experiment_ids': ['123'], 'filter': "status = 'OK'", 'max_results': 10}

    search_response = {
      'traces': [
        {
          'trace_id': 'tr-123',
          'trace_info': {'experiment_id': '123', 'status': 'OK', 'timestamp_ms': 1234567890},
        }
      ],
      'next_page_token': None,
    }

    mock_mlflow_functions.search_traces.return_value = search_response

    response = client.post('/api/mlflow/traces/search', json=search_request)

    assert response.status_code == 200
    data = response.json()
    assert len(data['traces']) == 1
    assert data['traces'][0]['trace_id'] == 'tr-123'
    mock_mlflow_functions.search_traces.assert_called_once_with(search_request)

  def test_get_trace_success(self, client, mock_mlflow_functions):
    """Test getting a specific trace."""
    trace_data = {
      'trace_id': 'tr-123',
      'trace_info': {
        'experiment_id': '123',
        'status': 'OK',
        'timestamp_ms': 1234567890,
        'execution_time_ms': 500,
      },
      'trace_data': {
        'spans': [
          {
            'name': 'main',
            'span_type': 'CHAIN',
            'start_time': 1234567890,
            'end_time': 1234568390,
            'status': 'OK',
          }
        ]
      },
    }

    mock_mlflow_functions.get_trace.return_value = trace_data

    response = client.get('/api/mlflow/traces/tr-123')

    assert response.status_code == 200
    data = response.json()
    assert data['trace_id'] == 'tr-123'
    assert len(data['trace_data']['spans']) == 1
    mock_mlflow_functions.get_trace.assert_called_once_with('tr-123')

  def test_get_trace_metadata_success(self, client, mock_mlflow_functions):
    """Test getting trace metadata."""
    metadata = {
      'trace_id': 'tr-123',
      'trace_info': {'experiment_id': '123', 'status': 'OK'},
      'span_names': ['main', 'llm_call', 'tool_call'],
    }

    mock_mlflow_functions.get_trace_data.return_value = metadata

    response = client.get('/api/mlflow/traces/tr-123/metadata')

    assert response.status_code == 200
    data = response.json()
    assert data['trace_id'] == 'tr-123'
    assert len(data['span_names']) == 3
    mock_mlflow_functions.get_trace_data.assert_called_once_with('tr-123')

  def test_link_traces_to_run_success(self, client, mock_mlflow_functions):
    """Test linking traces to a run."""
    link_request = {'run_id': 'run-123', 'trace_ids': ['tr-1', 'tr-2', 'tr-3']}

    link_response = {'linked_count': 3, 'run_id': 'run-123'}

    mock_mlflow_functions.link_traces_to_run.return_value = link_response

    response = client.post('/api/mlflow/traces/link-to-run', json=link_request)

    assert response.status_code == 200
    data = response.json()
    assert data['linked_count'] == 3
    assert data['run_id'] == 'run-123'
    mock_mlflow_functions.link_traces_to_run.assert_called_once_with(link_request)

  def test_create_run_success(self, client, mock_mlflow_functions):
    """Test creating a new MLflow run."""
    create_request = {
      'experiment_id': '123',
      'run_name': 'Test Run',
      'tags': {'purpose': 'labeling'},
    }

    created_run = {
      'run': {
        'info': {
          'run_id': 'run-new',
          'experiment_id': '123',
          'run_name': 'Test Run',
          'status': 'RUNNING',
        }
      }
    }

    mock_mlflow_functions.create_run.return_value = created_run

    response = client.post('/api/mlflow/runs', json=create_request)

    assert response.status_code == 200
    data = response.json()
    assert data['run']['info']['run_id'] == 'run-new'
    mock_mlflow_functions.create_run.assert_called_once_with(create_request)

  def test_update_run_success(self, client, mock_mlflow_functions):
    """Test updating an MLflow run."""
    update_request = {'run_id': 'run-123', 'status': 'FINISHED', 'end_time': 1234567890}

    updated_run = {
      'run': {'info': {'run_id': 'run-123', 'status': 'FINISHED', 'end_time': 1234567890}}
    }

    mock_mlflow_functions.update_run.return_value = updated_run

    response = client.patch('/api/mlflow/runs', json=update_request)

    assert response.status_code == 200
    data = response.json()
    assert data['run']['info']['status'] == 'FINISHED'
    mock_mlflow_functions.update_run.assert_called_once_with(update_request)
