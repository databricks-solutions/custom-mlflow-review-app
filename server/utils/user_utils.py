"""User utility functions with caching for Databricks operations."""

import logging
import time
from functools import lru_cache
from typing import Any, Dict

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User

logger = logging.getLogger(__name__)


class UserUtils:
  """Utility for User operations with intelligent caching."""

  def __init__(self):
    """Initialize with Databricks workspace client."""
    logger.info('🔧 [USER UTILS] Initializing WorkspaceClient...')
    init_start = time.time()
    self.client = WorkspaceClient()
    init_time = time.time() - init_start
    logger.info(f'✅ [USER UTILS] WorkspaceClient initialized in {init_time * 1000:.1f}ms')

    # Per-user cache for formatted user info (keyed by email)
    # This cache stores already-formatted user data to avoid re-processing
    self._user_info_cache: Dict[str, dict] = {}
    self._user_info_cache_times: Dict[str, float] = {}
    self._user_cache_ttl: float = 60 * 60  # 1 hour TTL for user data

  def _get_raw_user(self) -> User:
    """Get the current authenticated user from Databricks API."""
    logger.info('🌐 [USER UTILS] Fetching current user from Databricks API...')
    fetch_start = time.time()
    user = self.client.current_user.me()
    fetch_time = time.time() - fetch_start
    logger.info(
      f'✅ [USER UTILS] Current user fetched in {fetch_time * 1000:.1f}ms '
      f'(user: {user.user_name})'
    )
    return user

  def get_current_user(self) -> Dict[str, Any]:
    """Get current user information from Databricks."""
    logger.info('📊 [USER UTILS] Getting user info...')
    start_time = time.time()
    user = self._get_raw_user()

    result = {
      'userName': user.user_name or 'unknown',
      'displayName': user.display_name,
      'active': user.active or False,
      'emails': [email.value for email in (user.emails or [])],
      'groups': [group.display for group in (user.groups or [])],
    }

    total_time = time.time() - start_time
    logger.info(f'✅ [USER UTILS] User info retrieved in {total_time * 1000:.1f}ms')
    return result

  def get_current_user_cached_by_email(self, email: str) -> Dict[str, Any]:
    """Get user information with per-email caching.

    This method caches user data keyed by email address, allowing safe
    caching in multi-user environments. Use this when you already know
    the user's email address to avoid redundant API calls.

    Args:
        email: The user's email address to use as cache key

    Returns:
        Formatted user information dictionary
    """
    current_time = time.time()

    # Check cache for this specific email
    if email in self._user_info_cache:
      cache_age = current_time - self._user_info_cache_times[email]
      if cache_age < self._user_cache_ttl:
        logger.info(
          f'📋 [USER UTILS] Cache hit for {email} '
          f'(age: {cache_age:.1f}s, TTL: {self._user_cache_ttl}s)'
        )
        return self._user_info_cache[email]
      else:
        logger.info(f'⏰ [USER UTILS] Cache expired for {email} (age: {cache_age:.1f}s)')

    # Cache miss or expired - fetch fresh data
    logger.info(f'🔄 [USER UTILS] Cache miss for {email}, fetching fresh data...')
    user_info = self.get_current_user()

    # Verify the email matches (safety check)
    if email in user_info.get('emails', []):
      # Update cache for this email
      self._user_info_cache[email] = user_info
      self._user_info_cache_times[email] = current_time
      logger.info(f'💾 [USER UTILS] Cached user info for {email}')
    else:
      logger.warning(
        f'⚠️ [USER UTILS] Email mismatch: requested {email}, ' f'got {user_info.get("emails", [])}'
      )

    return user_info

  @lru_cache(maxsize=1)
  def _get_workspace_info(self) -> dict:
    """Get workspace information with caching.

    This method is cached for the lifetime of the UserUtils instance,
    which is appropriate since workspace information doesn't change.
    """
    logger.info('🌐 [USER UTILS] Loading workspace info (this should only happen once)')
    workspace_url = self.client.config.host
    workspace_info = {
      'url': workspace_url,
      'deployment_name': workspace_url.split('//')[1].split('.')[0] if workspace_url else None,
    }
    logger.info(f'✅ [USER UTILS] Workspace info loaded: {workspace_info["deployment_name"]}')
    return workspace_info

  def get_user_workspace_info(self) -> Dict[str, Any]:
    """Get user information along with workspace details."""
    user = self._get_raw_user()
    workspace_info = self._get_workspace_info()

    return {
      'user': {
        'userName': user.user_name or 'unknown',
        'displayName': user.display_name,
        'active': user.active or False,
      },
      'workspace': workspace_info,
    }

  def get_username(self) -> str:
    """Get the current user's username."""
    user_info = self.get_current_user()
    return user_info.get('userName', 'unknown')

  def get_display_name(self) -> str:
    """Get the current user's display name."""
    user_info = self.get_current_user()
    return user_info.get('displayName') or user_info.get('userName', 'unknown')

  def get_workspace_url(self) -> str:
    """Get the current workspace URL."""
    workspace_info = self._get_workspace_info()
    return workspace_info.get('url', '')


# Create a global instance for easy access
user_utils = UserUtils()
