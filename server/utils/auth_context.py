"""Authentication context for Databricks APIs and utilities."""

import os
from typing import Any, Dict, Optional

from databricks.sdk import WorkspaceClient


class AuthContext:
  """Authentication context that supports both token and profile-based auth."""

  def __init__(self, token: Optional[str] = None, profile: Optional[str] = None):
    """Initialize auth context.

    Args:
        token: Databricks access token (from OBO or environment)
        profile: Databricks config profile name
    """
    self.token = token
    self.profile = profile
    self._client_cache: Optional[WorkspaceClient] = None

  @classmethod
  def from_env(cls) -> 'AuthContext':
    """Create auth context from environment variables."""
    token = os.getenv('DATABRICKS_TOKEN')
    profile = os.getenv('DATABRICKS_CONFIG_PROFILE')
    return cls(token=token, profile=profile)

  @classmethod
  def from_obo_token(cls, token: str) -> 'AuthContext':
    """Create auth context from OBO token."""
    return cls(token=token)

  def get_workspace_client(self) -> WorkspaceClient:
    """Get WorkspaceClient configured with this auth context."""
    if self._client_cache is None:
      if self.token:
        # Use token-based auth
        self._client_cache = WorkspaceClient(token=self.token)
      elif self.profile:
        # Use profile-based auth
        self._client_cache = WorkspaceClient(profile=self.profile)
      else:
        # Use default auth (environment variables)
        self._client_cache = WorkspaceClient()

    return self._client_cache

  def get_auth_headers(self) -> Dict[str, str]:
    """Get HTTP headers for API requests."""
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    if self.token:
      headers['Authorization'] = f'Bearer {self.token}'
    else:
      # Fallback to WorkspaceClient to get token
      client = self.get_workspace_client()
      if hasattr(client.config, 'token') and client.config.token:
        headers['Authorization'] = f'Bearer {client.config.token}'

    return headers

  def get_databricks_host(self) -> str:
    """Get Databricks workspace host."""
    client = self.get_workspace_client()
    return client.config.host or os.getenv('DATABRICKS_HOST', '')

  def get_sql_connection_params(self) -> Dict[str, Any]:
    """Get parameters for Databricks SQL connection."""
    host = self.get_databricks_host()
    http_path = os.getenv('DATABRICKS_HTTP_PATH', '/sql/1.0/warehouses/DEFAULT')

    params = {
      'server_hostname': host.replace('https://', ''),
      'http_path': http_path,
    }

    if self.token:
      params['access_token'] = self.token
    else:
      # Let databricks-sql-connector use default auth
      pass

    return params

  def __repr__(self) -> str:
    if self.token:
      return f'AuthContext(token={self.token[:20]}...)'
    elif self.profile:
      return f'AuthContext(profile={self.profile})'
    else:
      return 'AuthContext(default)'
