"""Error handling middleware for the FastAPI application.

This middleware catches all exceptions and formats them consistently for the client,
ensuring that error messages are properly logged and returned in a standardized format.
"""

import logging
import os
import traceback
from typing import Any, Dict
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from server.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
  """Middleware that handles all exceptions and returns standardized error responses."""

  async def dispatch(self, request: Request, call_next):
    """Process the request and handle any exceptions that occur."""
    # Generate a unique request ID for correlation
    request_id = str(uuid4())
    request.state.request_id = request_id

    try:
      response = await call_next(request)
      return response
    except Exception as exc:
      return await self._handle_exception(request, exc, request_id)

  async def _handle_exception(
    self, request: Request, exc: Exception, request_id: str
  ) -> JSONResponse:
    """Handle an exception and return a formatted error response."""
    # Build base error response
    error_response = self._build_error_response(exc, request_id)

    # Log the error
    self._log_error(request, exc, request_id, error_response['status_code'])

    # Return JSON response
    return JSONResponse(status_code=error_response['status_code'], content=error_response)

  def _build_error_response(self, exc: Exception, request_id: str) -> Dict[str, Any]:
    """Build a standardized error response."""
    # Check if we're in development mode (look for common dev environment indicators)
    is_development = (
      os.getenv('ENVIRONMENT', '').lower() in ['dev', 'development', 'local']
      or os.getenv('DEBUG', '').lower() in ['true', '1', 'yes']
      or os.getenv('FASTAPI_ENV', '').lower() == 'development'
    )

    if isinstance(exc, AppException):
      # Custom application exception
      return {
        'error': {
          'message': exc.message,
          'code': exc.error_code,
          'details': exc.details,
        },
        'request_id': request_id,
        'status_code': exc.status_code,
      }
    else:
      # Unexpected exception - show details in development mode
      error_details = {}

      if is_development:
        # In development, include detailed error information
        error_details = {
          'error_type': type(exc).__name__,
          'error_message': str(exc),
          'traceback': traceback.format_exc().split('\n'),
        }

        # If it's a validation error from Pydantic or similar, include more context
        if hasattr(exc, 'errors'):
          error_details['validation_errors'] = exc.errors()

        message = f'{type(exc).__name__}: {str(exc)}'
      else:
        # In production, use generic message
        message = 'An unexpected error occurred'

      return {
        'error': {
          'message': message,
          'code': 'INTERNAL_SERVER_ERROR',
          'details': error_details,
        },
        'request_id': request_id,
        'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
      }

  def _log_error(self, request: Request, exc: Exception, request_id: str, status_code: int) -> None:
    """Log error details for debugging."""
    error_details = {
      'request_id': request_id,
      'method': request.method,
      'path': request.url.path,
      'status_code': status_code,
      'error_type': type(exc).__name__,
      'error_message': str(exc),
    }

    # Add query parameters if present
    if request.url.query:
      error_details['query_params'] = request.url.query

    # Log based on severity
    if isinstance(exc, AppException):
      # Known application errors
      if status_code >= 500:
        logger.error(
          f'Application error: {exc.message}',
          extra=error_details,
          exc_info=False,  # Don't include full traceback for known errors
        )
      else:
        logger.warning(f'Client error: {exc.message}', extra=error_details)
    else:
      # Unexpected errors - always log with full traceback
      logger.error(
        f'Unexpected error: {str(exc)}',
        extra=error_details,
        exc_info=True,  # Include full traceback
      )
