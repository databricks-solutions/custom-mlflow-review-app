"""FastAPI performance profiling middleware."""

import cProfile
import io
import pstats
import time
import traceback
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ProfilerMiddleware(BaseHTTPMiddleware):
  """Middleware to profile slow endpoints and log detailed performance information."""

  def __init__(self, app, slow_threshold_ms: int = 1000):
    super().__init__(app)
    self.slow_threshold_ms = slow_threshold_ms

  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    import logging

    logger = logging.getLogger(__name__)

    start_time = time.time()
    method = request.method
    path = request.url.path

    # Profile the request
    profiler = cProfile.Profile()
    profiler.enable()

    try:
      # Execute the request
      response = await call_next(request)

      # Stop profiling
      profiler.disable()

      # Calculate timing
      total_time = time.time() - start_time
      total_ms = total_time * 1000

      # Log basic timing
      if total_ms > self.slow_threshold_ms:
        logger.warning(f'🐌 [SLOW ENDPOINT] {method} {path} took {total_ms:.1f}ms')

        # Generate profile stats for slow requests
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 slowest functions

        logger.info(f'🔍 [PROFILE] Top 20 functions for {method} {path}:\\n{s.getvalue()}')
      else:
        logger.info(f'✅ [TIMING] {method} {path} completed in {total_ms:.1f}ms')

      # Add timing header
      response.headers['X-Response-Time'] = f'{total_ms:.1f}ms'

      return response

    except Exception as e:
      profiler.disable()
      error_time = time.time() - start_time
      error_ms = error_time * 1000

      logger.error(f'❌ [ERROR] {method} {path} failed after {error_ms:.1f}ms: {str(e)}')
      logger.error(f'🔍 [TRACEBACK] {traceback.format_exc()}')

      # Still generate profile for failed requests if they were slow
      if error_ms > self.slow_threshold_ms:
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 for failed requests

        logger.error(f'🔍 [ERROR_PROFILE] Functions before failure:\\n{s.getvalue()}')

      raise


class DetailedTimingMiddleware(BaseHTTPMiddleware):
  """Middleware to add detailed timing information without heavy profiling."""

  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    import logging

    logger = logging.getLogger(__name__)

    start_time = time.time()
    method = request.method
    path = request.url.path

    # Log request start
    logger.info(f'🚀 [REQUEST START] {method} {path}')

    try:
      response = await call_next(request)

      total_time = time.time() - start_time
      total_ms = total_time * 1000

      # Log completion with status
      logger.info(f'✅ [REQUEST END] {method} {path} - {response.status_code} - {total_ms:.1f}ms')

      # Add detailed headers
      response.headers['X-Response-Time'] = f'{total_ms:.1f}ms'
      response.headers['X-Response-Status'] = str(response.status_code)

      return response

    except Exception as e:
      error_time = time.time() - start_time
      error_ms = error_time * 1000

      logger.error(f'❌ [REQUEST ERROR] {method} {path} failed after {error_ms:.1f}ms: {str(e)}')
      raise


class BlockingOperationDetector(BaseHTTPMiddleware):
  """Middleware to detect potentially blocking operations in async routes."""

  def __init__(self, app, warning_threshold_ms: int = 100):
    super().__init__(app)
    self.warning_threshold_ms = warning_threshold_ms

  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    method = request.method
    path = request.url.path

    # Track if we're in an async context
    loop_start_time = time.time()

    try:
      # Measure event loop blocking
      before_yield = time.time()
      await asyncio.sleep(0)  # Yield control to event loop
      after_yield = time.time()

      yield_time = (after_yield - before_yield) * 1000

      if yield_time > self.warning_threshold_ms:
        logger.warning(
          f'⚠️ [EVENT LOOP BLOCKED] {method} {path} - Event loop blocked for {yield_time:.1f}ms before request'
        )

      # Execute the request
      response = await call_next(request)

      return response

    except Exception as e:
      logger.error(f'❌ [BLOCKING DETECTOR ERROR] {method} {path}: {str(e)}')
      raise
