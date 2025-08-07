"""User utility functions for direct use as tools by Claude."""

from typing import Any, Dict

from server.services.user_service import UserService


class UserUtils:
  """Simplified utility for User operations."""

  def __init__(self):
    """Initialize with UserService."""
    self.user_service = UserService()

  def get_current_user(self) -> Dict[str, Any]:
    """Get current user information from Databricks."""
    return self.user_service.get_user_info()

  def get_user_workspace_info(self) -> Dict[str, Any]:
    """Get user information along with workspace details."""
    return self.user_service.get_user_workspace_info()

  def get_username(self) -> str:
    """Get the current user's username."""
    user_info = self.user_service.get_user_info()
    return user_info.get('userName', 'unknown')

  def get_display_name(self) -> str:
    """Get the current user's display name."""
    user_info = self.user_service.get_user_info()
    return user_info.get('displayName') or user_info.get('userName', 'unknown')

  def get_workspace_url(self) -> str:
    """Get the current workspace URL."""
    workspace_info = self.user_service.get_user_workspace_info()
    return workspace_info.get('workspace', {}).get('url', '')


# Create a global instance for easy access
user_utils = UserUtils()
