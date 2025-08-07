"""Tests for custom exception classes.

This module tests the custom exception hierarchy and error handling
functionality of the MLflow Review App.
"""

from server.exceptions import (
  AppException,
  AuthenticationError,
  AuthorizationError,
  ConfigurationError,
  DatabricksAPIError,
  MLflowError,
  NotFoundError,
  ValidationError,
)


class TestAppException:
  """Test the base AppException class."""

  def test_basic_exception(self):
    """Test basic exception creation."""
    exc = AppException('Test message')

    assert str(exc) == 'Test message'
    assert exc.message == 'Test message'
    assert exc.status_code == 500
    assert exc.error_code == 'AppException'
    assert exc.details == {}

  def test_exception_with_all_params(self):
    """Test exception with all parameters."""
    details = {'field': 'value', 'context': 'test'}
    exc = AppException(
      message='Custom message', status_code=400, error_code='CUSTOM_ERROR', details=details
    )

    assert exc.message == 'Custom message'
    assert exc.status_code == 400
    assert exc.error_code == 'CUSTOM_ERROR'
    assert exc.details == details


class TestNotFoundError:
  """Test the NotFoundError exception."""

  def test_not_found_error(self):
    """Test NotFoundError creation."""
    exc = NotFoundError('User', '123')

    assert exc.message == "User with identifier '123' not found"
    assert exc.status_code == 404
    assert exc.error_code == 'RESOURCE_NOT_FOUND'
    assert exc.details == {'resource': 'User', 'identifier': '123'}


class TestValidationError:
  """Test the ValidationError exception."""

  def test_validation_error_basic(self):
    """Test basic ValidationError."""
    exc = ValidationError('Invalid input')

    assert exc.message == 'Invalid input'
    assert exc.status_code == 400
    assert exc.error_code == 'VALIDATION_ERROR'
    assert exc.details == {}

  def test_validation_error_with_field(self):
    """Test ValidationError with field specification."""
    exc = ValidationError('Field is required', field='experiment_id')

    assert exc.message == 'Field is required'
    assert exc.details == {'field': 'experiment_id'}


class TestMLflowError:
  """Test the MLflowError exception."""

  def test_mlflow_error(self):
    """Test MLflowError creation."""
    exc = MLflowError('Failed to get trace', 'get_trace')

    assert exc.message == 'MLflow operation failed: Failed to get trace'
    assert exc.status_code == 500
    assert exc.error_code == 'MLFLOW_ERROR'
    assert exc.details == {'operation': 'get_trace'}


class TestExceptionInheritance:
  """Test exception inheritance and isinstance checks."""

  def test_exception_inheritance(self):
    """Test that all custom exceptions inherit from AppException."""
    exceptions = [
      NotFoundError('Resource', '123'),
      ValidationError('Invalid'),
      AuthenticationError(),
      AuthorizationError(),
      DatabricksAPIError('Error', '/api/path'),
      MLflowError('Error', 'operation'),
      ConfigurationError('Error'),
    ]

    for exc in exceptions:
      assert isinstance(exc, AppException)
      assert isinstance(exc, Exception)
