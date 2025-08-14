"""Simple test for MLflow router to check basic functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from server.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_search_traces_endpoint_exists(client):
    """Test that search traces endpoint exists."""
    # Mock the MLflow search function to return empty list
    with patch('server.routers.mlflow.mlflow.mlflow_search_traces') as mock_search:
        # Also mock the preview extraction to avoid issues
        with patch('server.routers.mlflow.mlflow._extract_request_response_preview') as mock_preview:
            mock_search.return_value = []  # Return empty list of traces
            mock_preview.return_value = (None, None)
            
            response = client.post('/api/mlflow/search-traces', json={
                'experiment_ids': ['123'],
                'max_results': 10
            })
            
            assert response.status_code == 200
            data = response.json()
            assert 'traces' in data
            assert data['traces'] == []
            assert data['next_page_token'] is None
            
            
def test_get_trace_endpoint_exists(client):
    """Test that get trace endpoint exists."""
    # Create a simple mock trace
    mock_trace = MagicMock()
    mock_trace.to_dict.return_value = {
        'info': {'trace_id': 'tr-123'},
        'data': {'spans': []}
    }
    
    with patch('server.routers.mlflow.mlflow.mlflow_get_trace') as mock_get:
        with patch('server.routers.mlflow.mlflow._extract_request_response_preview') as mock_preview:
            mock_get.return_value = mock_trace
            mock_preview.return_value = (None, None)
            
            response = client.get('/api/mlflow/traces/tr-123')
            
            assert response.status_code == 200
            data = response.json()
            assert data['info']['trace_id'] == 'tr-123'