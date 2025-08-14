"""Tests for error handler middleware.

This module tests the error handling middleware functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from server.exceptions import AppException, NotFoundError, ValidationError
from server.middleware.error_handler import ErrorHandlerMiddleware


@pytest.fixture
def app():
  """Create a test FastAPI app with error handler."""
  test_app = FastAPI()
  test_app.add_middleware(ErrorHandlerMiddleware)

  @test_app.get('/test/success')
  async def success_endpoint():
    return {'status': 'ok'}

  @test_app.get('/test/app-exception')
  async def app_exception_endpoint():
    raise AppException('Test error', status_code=400, error_code='TEST_ERROR')

  @test_app.get('/test/not-found')
  async def not_found_endpoint():
    raise NotFoundError('User', '123')

  @test_app.get('/test/validation-error')
  async def validation_endpoint():
    raise ValidationError('Invalid input', field='test_field')

  @test_app.get('/test/generic-exception')
  async def generic_exception_endpoint():
    raise ValueError('Something went wrong')

  return test_app


@pytest.fixture
def client(app):
  """Create test client."""
  return TestClient(app)


class TestErrorHandlerMiddleware:
  """Test the ErrorHandlerMiddleware."""

  def test_successful_request(self, client):
    """Test that successful requests pass through."""
    response = client.get('/test/success')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}

  def test_app_exception_handling(self, client):
    """Test handling of AppException."""
    response = client.get('/test/app-exception')
    assert response.status_code == 400

    data = response.json()
    assert 'error' in data
    assert data['error']['message'] == 'Test error'
    assert data['error']['code'] == 'TEST_ERROR'
    assert 'request_id' in data

  def test_not_found_exception(self, client):
    """Test handling of NotFoundError."""
    response = client.get('/test/not-found')
    assert response.status_code == 404

    data = response.json()
    assert data['error']['message'] == "User with identifier '123' not found"
    assert data['error']['code'] == 'RESOURCE_NOT_FOUND'
    assert data['error']['details']['resource'] == 'User'
    assert data['error']['details']['identifier'] == '123'

  def test_validation_error(self, client):
    """Test handling of ValidationError."""
    response = client.get('/test/validation-error')
    assert response.status_code == 400

    data = response.json()
    assert data['error']['message'] == 'Invalid input'
    assert data['error']['code'] == 'VALIDATION_ERROR'
    assert data['error']['details']['field'] == 'test_field'

  def test_generic_exception(self, client):
    """Test handling of generic exceptions."""
    response = client.get('/test/generic-exception')
    assert response.status_code == 500

    data = response.json()
    assert data['error']['message'] == 'An unexpected error occurred'
    assert data['error']['code'] == 'INTERNAL_ERROR'
    assert 'request_id' in data


class TestErrorHandlerMiddlewareMethods:
  """Test the internal methods of ErrorHandlerMiddleware."""

  def test_build_error_response_app_exception(self):
    """Test building error response for AppException."""
    middleware = ErrorHandlerMiddleware(None)
    request_id = 'test-request-123'

    exc = ValidationError('Invalid data', field='email')
    response = middleware._build_error_response(exc, request_id)

    assert response['error']['message'] == 'Invalid data'
    assert response['error']['code'] == 'VALIDATION_ERROR'
    assert response['error']['details']['field'] == 'email'
    assert response['status_code'] == 400
    assert response['request_id'] == request_id

  def test_build_error_response_generic_exception(self):
    """Test building error response for generic exception."""
    middleware = ErrorHandlerMiddleware(None)
    request_id = 'test-request-123'

    exc = ValueError('Something went wrong')
    response = middleware._build_error_response(exc, request_id)

    assert response['error']['message'] == 'An unexpected error occurred'
    assert response['error']['code'] == 'INTERNAL_SERVER_ERROR'
    assert response['error']['details'] == {}
    assert response['status_code'] == 500
    assert response['request_id'] == request_id

  @patch('server.middleware.error_handler.logger')
  def test_log_error_app_exception(self, mock_logger):
    """Test logging for AppException."""
    middleware = ErrorHandlerMiddleware(None)
    request = Mock(spec=Request)
    request.method = 'GET'
    request.url = Mock(path='/test/path', query='')

    exc = NotFoundError('User', '123')
    middleware._log_error(request, exc, 'test-123', 404)

    mock_logger.warning.assert_called_once()
    log_message = mock_logger.warning.call_args[0][0]
    assert "User with identifier '123' not found" in log_message

  @patch('server.middleware.error_handler.logger')
  def test_log_error_server_error(self, mock_logger):
    """Test logging for server errors."""
    middleware = ErrorHandlerMiddleware(None)
    request = Mock(spec=Request)
    request.method = 'POST'
    request.url = Mock(path='/api/endpoint', query='')

    exc = ValueError('Unexpected error')
    middleware._log_error(request, exc, 'test-123', 500)

    mock_logger.error.assert_called_once()
    assert mock_logger.error.call_args[1]['exc_info'] is True
