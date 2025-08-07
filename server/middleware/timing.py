"""Timing middleware for comprehensive performance tracking."""

import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TimingMiddleware(BaseHTTPMiddleware):
  """Middleware to track request timing and performance metrics."""

  def __init__(self, app, logger_name: str = 'timing'):
    super().__init__(app)
    self.logger = logging.getLogger(logger_name)

    # Configure detailed logging
    if not self.logger.handlers:
      handler = logging.StreamHandler()
      formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      handler.setFormatter(formatter)
      self.logger.addHandler(handler)
      self.logger.setLevel(logging.INFO)

  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    """Process request with detailed timing and logging."""
    # Generate unique request ID for correlation
    request_id = str(uuid.uuid4())[:8]

    # Record request start
    start_time = time.time()
    start_time_ns = time.time_ns()

    # Extract request details
    method = request.method
    path = request.url.path
    query_params = dict(request.query_params)

    # Log request start
    self.logger.info(f'🚀 [REQ-{request_id}] {method} {path} - START')

    # Add timing context to request state
    request.state.request_id = request_id
    request.state.start_time = start_time
    request.state.start_time_ns = start_time_ns

    try:
      # Process request
      response = await call_next(request)

      # Record response timing
      end_time = time.time()
      end_time_ns = time.time_ns()
      duration_ms = (end_time - start_time) * 1000
      duration_ns = end_time_ns - start_time_ns

      # Get response details
      status_code = response.status_code
      response_size = 0

      # Try to estimate response size
      if hasattr(response, 'body'):
        if isinstance(response.body, bytes):
          response_size = len(response.body)
        elif isinstance(response.body, str):
          response_size = len(response.body.encode('utf-8'))

      # Categorize performance
      perf_category = self._categorize_performance(duration_ms, path)

      # Log detailed timing information
      timing_info = {
        'request_id': request_id,
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 3),
        'duration_ns': duration_ns,
        'response_size_bytes': response_size,
        'performance_category': perf_category,
        'query_params_count': len(query_params),
      }

      # Add performance warnings
      warnings = []
      if duration_ms > 5000:
        warnings.append('VERY_SLOW')
      elif duration_ms > 2000:
        warnings.append('SLOW')
      elif duration_ms > 1000:
        warnings.append('MODERATE')

      if response_size > 10 * 1024 * 1024:  # 10MB
        warnings.append('LARGE_RESPONSE')
      elif response_size > 1024 * 1024:  # 1MB
        warnings.append('MEDIUM_RESPONSE')

      if warnings:
        timing_info['warnings'] = warnings

      # Log completion with appropriate level
      log_level = self._get_log_level(duration_ms, status_code)
      log_message = (
        f'✅ [REQ-{request_id}] {method} {path} - COMPLETE {status_code} in {duration_ms:.1f}ms'
      )

      if warnings:
        log_message += f' ⚠️ {",".join(warnings)}'

      if log_level == logging.WARNING:
        self.logger.warning(log_message)
      elif log_level == logging.ERROR:
        self.logger.error(log_message)
      else:
        self.logger.info(log_message)

      # Add detailed JSON timing info for analysis
      self.logger.info(f'📊 [TIMING-{request_id}] {json.dumps(timing_info)}')

      # Add timing headers to response
      response.headers['X-Request-ID'] = request_id
      response.headers['X-Response-Time-MS'] = str(round(duration_ms, 3))
      response.headers['X-Performance-Category'] = perf_category

      return response

    except Exception as e:
      # Record error timing
      end_time = time.time()
      duration_ms = (end_time - start_time) * 1000

      # Log error with timing
      self.logger.error(
        f'❌ [REQ-{request_id}] {method} {path} - ERROR after {duration_ms:.1f}ms: {str(e)}'
      )

      # Re-raise the exception
      raise

  def _categorize_performance(self, duration_ms: float, path: str) -> str:
    """Categorize request performance based on duration and endpoint type."""
    # Special handling for known slow endpoints
    if '/traces/' in path or '/search-traces' in path:
      if duration_ms > 3000:
        return 'CRITICAL_SLOW'
      elif duration_ms > 1500:
        return 'SLOW'
      elif duration_ms > 800:
        return 'MODERATE'
      else:
        return 'ACCEPTABLE'

    # General endpoint categorization
    if duration_ms > 5000:
      return 'CRITICAL_SLOW'
    elif duration_ms > 2000:
      return 'SLOW'
    elif duration_ms > 1000:
      return 'MODERATE'
    elif duration_ms > 500:
      return 'ACCEPTABLE'
    else:
      return 'FAST'

  def _get_log_level(self, duration_ms: float, status_code: int) -> int:
    """Determine appropriate log level based on performance and status."""
    if status_code >= 500:
      return logging.ERROR
    elif status_code >= 400:
      return logging.WARNING
    elif duration_ms > 5000:
      return logging.ERROR
    elif duration_ms > 2000:
      return logging.WARNING
    else:
      return logging.INFO


class OperationTimer:
  """Context manager for timing specific operations within requests."""

  def __init__(self, operation_name: str, request_id: str = 'unknown'):
    self.operation_name = operation_name
    self.request_id = request_id
    self.logger = logging.getLogger('operation_timing')
    self.start_time = None
    self.start_time_ns = None

    # Configure logger if needed
    if not self.logger.handlers:
      handler = logging.StreamHandler()
      formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      handler.setFormatter(formatter)
      self.logger.addHandler(handler)
      self.logger.setLevel(logging.INFO)

  def __enter__(self):
    """Start timing operation."""
    self.start_time = time.time()
    self.start_time_ns = time.time_ns()

    self.logger.info(f'🔧 [OP-{self.request_id}] {self.operation_name} - START')
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """End timing operation and log results."""
    end_time = time.time()
    end_time_ns = time.time_ns()

    duration_ms = (end_time - self.start_time) * 1000
    duration_ns = end_time_ns - self.start_time_ns

    if exc_type is not None:
      # Operation failed
      self.logger.error(
        f'❌ [OP-{self.request_id}] {self.operation_name} - '
        f'FAILED after {duration_ms:.1f}ms: {exc_val}'
      )
    else:
      # Operation succeeded
      log_level = logging.WARNING if duration_ms > 1000 else logging.INFO
      status_emoji = '⚠️' if duration_ms > 1000 else '✅'

      message = (
        f'{status_emoji} [OP-{self.request_id}] {self.operation_name} - '
        f'COMPLETE in {duration_ms:.1f}ms'
      )

      if log_level == logging.WARNING:
        self.logger.warning(message)
      else:
        self.logger.info(message)

    # Log detailed JSON timing for analysis
    timing_data = {
      'request_id': self.request_id,
      'operation': self.operation_name,
      'duration_ms': round(duration_ms, 3),
      'duration_ns': duration_ns,
      'success': exc_type is None,
    }

    if exc_type is not None:
      timing_data['error'] = str(exc_val)

    self.logger.info(f'📈 [OP-TIMING-{self.request_id}] {json.dumps(timing_data)}')


def get_request_timer(request: Request, operation_name: str) -> OperationTimer:
  """Get an operation timer for the current request context."""
  request_id = getattr(request.state, 'request_id', 'unknown')
  return OperationTimer(operation_name, request_id)
