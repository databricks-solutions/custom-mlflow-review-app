"""User service for Databricks user operations."""

import time
from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User


class UserService:
  """Service for managing Databricks user operations."""

  def __init__(self):
    """Initialize the user service with Databricks workspace client."""
    self.client = WorkspaceClient()
    # Cache workspace info aggressively (24 hour TTL)
    self._workspace_info_cache: Optional[dict] = None
    self._workspace_info_cache_time: float = 0
    self._workspace_cache_ttl: float = 24 * 60 * 60  # 24 hours in seconds

  def get_current_user(self) -> User:
    """Get the current authenticated user."""
    return self.client.current_user.me()

  def get_user_info(self) -> dict:
    """Get formatted user information."""
    user = self.get_current_user()
    return {
      'userName': user.user_name or 'unknown',
      'displayName': user.display_name,
      'active': user.active or False,
      'emails': [email.value for email in (user.emails or [])],
      'groups': [group.display for group in (user.groups or [])],
    }

  def _get_workspace_info(self) -> dict:
    """Get workspace information with aggressive caching."""
    current_time = time.time()
    
    # Check if cache is still valid
    if (self._workspace_info_cache is not None and 
        current_time - self._workspace_info_cache_time < self._workspace_cache_ttl):
      return self._workspace_info_cache

    # Cache miss or expired - fetch fresh data
    workspace_url = self.client.config.host
    workspace_info = {
      'url': workspace_url,
      'deployment_name': workspace_url.split('//')[1].split('.')[0] if workspace_url else None,
    }
    
    # Update cache
    self._workspace_info_cache = workspace_info
    self._workspace_info_cache_time = current_time
    
    return workspace_info

  def get_user_workspace_info(self) -> dict:
    """Get user workspace information (workspace info is cached)."""
    user = self.get_current_user()
    workspace_info = self._get_workspace_info()

    return {
      'user': {
        'userName': user.user_name or 'unknown',
        'displayName': user.display_name,
        'active': user.active or False,
      },
      'workspace': workspace_info,
    }
