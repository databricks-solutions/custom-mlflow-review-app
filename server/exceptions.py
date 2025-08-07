"""Custom exceptions for the MLflow Review App.

This module defines custom exception classes that are used throughout the application
to provide consistent error handling and meaningful error messages to clients.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
  """Base exception class for all application exceptions."""

  def __init__(
    self,
    message: str,
    status_code: int = 500,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
  ):
    super().__init__(message)
    self.message = message
    self.status_code = status_code
    self.error_code = error_code or self.__class__.__name__
    self.details = details or {}


class NotFoundError(AppException):
  """Raised when a requested resource is not found."""

  def __init__(self, resource: str, identifier: str):
    super().__init__(
      message=f"{resource} with identifier '{identifier}' not found",
      status_code=404,
      error_code='RESOURCE_NOT_FOUND',
      details={'resource': resource, 'identifier': identifier},
    )


class ValidationError(AppException):
  """Raised when input validation fails."""

  def __init__(self, message: str, field: Optional[str] = None):
    details = {}
    if field:
      details['field'] = field
    super().__init__(
      message=message, status_code=400, error_code='VALIDATION_ERROR', details=details
    )


class AuthenticationError(AppException):
  """Raised when authentication fails."""

  def __init__(self, message: str = 'Authentication failed'):
    super().__init__(message=message, status_code=401, error_code='AUTHENTICATION_ERROR')


class AuthorizationError(AppException):
  """Raised when user lacks required permissions."""

  def __init__(self, message: str = 'Insufficient permissions'):
    super().__init__(message=message, status_code=403, error_code='AUTHORIZATION_ERROR')


class DatabricksAPIError(AppException):
  """Raised when Databricks API calls fail."""

  def __init__(self, message: str, api_path: str, response_code: Optional[int] = None):
    super().__init__(
      message=f'Databricks API error: {message}',
      status_code=502,
      error_code='DATABRICKS_API_ERROR',
      details={'api_path': api_path, 'upstream_status_code': response_code},
    )


class MLflowError(AppException):
  """Raised when MLflow operations fail."""

  def __init__(self, message: str, operation: str):
    super().__init__(
      message=f'MLflow operation failed: {message}',
      status_code=500,
      error_code='MLFLOW_ERROR',
      details={'operation': operation},
    )


class ConfigurationError(AppException):
  """Raised when configuration is invalid or missing."""

  def __init__(self, message: str, config_key: Optional[str] = None):
    details = {}
    if config_key:
      details['config_key'] = config_key
    super().__init__(
      message=message, status_code=500, error_code='CONFIGURATION_ERROR', details=details
    )
