"""Authentication middleware for extracting user tokens from Databricks Apps."""

from typing import Optional

from databricks.sdk import WorkspaceClient
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from server.utils.auth_context import AuthContext
from server.utils.config import get_config
from server.utils.permissions import get_user_role as determine_user_role, is_developer


class AuthMiddleware(BaseHTTPMiddleware):
  """Middleware to extract and store user authentication tokens.

  This middleware extracts the x-forwarded-access-token header from incoming requests
  (provided by Databricks Apps) and stores it in the request state for use by API endpoints.
  Falls back to WorkspaceClient authentication for local development.
  """

  async def dispatch(self, request: Request, call_next):
    """Extract user token and username from headers or environment and store in request state."""
    # Extract user token from Databricks Apps forwarded header
    user_token = request.headers.get('x-forwarded-access-token')

    # Check if this is an OBO request by detecting other x-forwarded-* headers
    # Databricks Apps provides user info via headers when running on behalf of a user
    forwarded_email = request.headers.get('x-forwarded-email')
    forwarded_user = request.headers.get('x-forwarded-user')
    forwarded_preferred_username = request.headers.get('x-forwarded-preferred-username')

    is_obo = bool(forwarded_email or forwarded_user or forwarded_preferred_username)

    print(
      f'AUTH DEBUG: user_token={bool(user_token)}, forwarded_email={forwarded_email}, '
      f'forwarded_user={forwarded_user}, is_obo={is_obo}'
    )

    # Fallback to WorkspaceClient for local development
    if not user_token and not is_obo:
      try:
        client = WorkspaceClient()
        user_token = client.config.token
      except Exception:
        # Silently fail - token will remain None
        pass

    # For OBO requests, use the headers provided by Databricks Apps
    username = None
    obo_user_info = None
    if is_obo:
      # Use the forwarded headers from Databricks Apps
      username = forwarded_email or forwarded_user or forwarded_preferred_username
      obo_user_info = {
        'userName': forwarded_email or forwarded_preferred_username or forwarded_user,
        'displayName': forwarded_preferred_username or forwarded_user or forwarded_email,
        'active': True,
        'emails': [forwarded_email] if forwarded_email else [],
      }
      print(f'AUTH DEBUG: Using OBO headers - username={username}, obo_user_info={obo_user_info}')
    elif user_token:
      # For non-OBO requests, get username from token
      try:
        client = WorkspaceClient(token=user_token)
        current_user = client.current_user.me()
        username = current_user.user_name
      except Exception:
        # Silently fail - username will remain None
        pass

    # Create auth context for utilities and tools
    # Always use service principal credentials from environment
    # OBO is only used for user identity, not for API authentication
    auth_context = AuthContext.from_env()

    # Determine user role (developer or sme) based on config
    user_role = 'sme'  # Default to SME
    user_is_developer = False
    experiment_id = None

    if username:
      user_role = determine_user_role(username)
      user_is_developer = is_developer(username)

      # Get experiment ID from config for permission checks
      try:
        config = get_config()
        experiment_id = config.experiment_id
      except Exception:
        pass

    # Store token, username, user info, auth context, role info, and OBO status in request state
    request.state.db_auth_token = user_token
    request.state.db_auth_username = username
    request.state.db_auth_user_info = obo_user_info
    request.state.db_auth_has_token = bool(user_token)
    request.state.db_auth_is_obo = is_obo
    request.state.db_auth_context = auth_context
    request.state.db_user_role = user_role
    request.state.db_user_is_developer = user_is_developer
    request.state.db_experiment_id = experiment_id

    response = await call_next(request)
    return response


def get_user_token(request: Request) -> Optional[str]:
  """Helper function to get user token from request state."""
  return getattr(request.state, 'db_auth_token', None)


def has_user_token(request: Request) -> bool:
  """Helper function to check if user token is available."""
  return getattr(request.state, 'db_auth_has_token', False)


def is_obo_request(request: Request) -> bool:
  """Helper function to check if request is using OBO (On-Behalf-Of) authentication."""
  return getattr(request.state, 'db_auth_is_obo', False)


def get_username(request: Request) -> Optional[str]:
  """Helper function to get username from request state."""
  return getattr(request.state, 'db_auth_username', None)


def get_obo_user_info(request: Request) -> Optional[dict]:
  """Helper function to get OBO user info from request state."""
  return getattr(request.state, 'db_auth_user_info', None)


def get_auth_context(request: Request) -> AuthContext:
  """Helper function to get auth context from request state."""
  auth_context = getattr(request.state, 'db_auth_context', None)
  if auth_context is None:
    # Fallback to environment-based auth
    auth_context = AuthContext.from_env()
  return auth_context


def get_user_role(request: Request) -> str:
  """Helper function to get user role from request state."""
  return getattr(request.state, 'db_user_role', 'sme')


def is_user_developer(request: Request) -> bool:
  """Helper function to check if user is a developer."""
  return getattr(request.state, 'db_user_is_developer', False)


def get_experiment_id(request: Request) -> Optional[str]:
  """Helper function to get experiment ID from request state."""
  return getattr(request.state, 'db_experiment_id', None)
