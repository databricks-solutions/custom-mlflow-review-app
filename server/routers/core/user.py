"""User router for Databricks user information."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from server.middleware import get_obo_user_info, has_user_token, is_obo_request
from server.middleware.auth import get_username, is_user_developer
from server.utils.user_utils import user_utils

router = APIRouter()


class UserInfo(BaseModel):
  """Databricks user information with authentication details and role."""

  userName: str
  displayName: str | None = None
  active: bool
  emails: list[str] = []
  # Auth middleware properties
  is_obo: bool = False
  has_token: bool = False
  # Role and permissions
  role: str = 'sme'  # 'developer' or 'sme'
  is_developer: bool = False
  can_access_dev_pages: bool = False


class UserWorkspaceInfo(BaseModel):
  """User and workspace information."""

  user: UserInfo
  workspace: dict


@router.get('/me', response_model=UserInfo)
def get_current_user(request: Request):
  """Get current user information from Databricks with auth details and role."""
  try:
    is_obo = is_obo_request(request)
    obo_user_info = get_obo_user_info(request)

    # Get role information
    username = get_username(request)
    is_dev = is_user_developer(request)
    user_role = 'developer' if is_dev else 'sme'

    # Debug: Check if we have the x-forwarded-access-token header
    has_forwarded_token = bool(request.headers.get('x-forwarded-access-token'))

    # Use OBO user info when available, otherwise fall back to service principal info
    if is_obo and obo_user_info:
      return UserInfo(
        userName=obo_user_info['userName'],
        displayName=obo_user_info['displayName'],
        active=obo_user_info['active'],
        emails=obo_user_info['emails'],
        # Auth middleware properties
        is_obo=is_obo,
        has_token=has_user_token(request),
        # Role and permissions
        role=user_role,
        is_developer=is_dev,
        can_access_dev_pages=is_dev,
      )
    else:
      # Fall back to service principal info for non-OBO requests
      user_info = user_utils.get_current_user()
      return UserInfo(
        userName=user_info['userName'],
        displayName=user_info['displayName'],
        active=user_info['active'],
        emails=user_info['emails'],
        # Auth middleware properties
        is_obo=has_forwarded_token,  # Override based on actual header presence
        has_token=has_user_token(request),
        # Role and permissions
        role=user_role,
        is_developer=is_dev,
        can_access_dev_pages=is_dev,
      )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get('/me/debug')
def debug_auth(request: Request):
  """Debug endpoint to see auth middleware state."""
  # Check all header variations
  headers_to_check = [
    'x-forwarded-access-token',
    'X-Forwarded-Access-Token',
    'X_FORWARDED_ACCESS_TOKEN',
    'authorization',
  ]

  header_debug = {}
  for header in headers_to_check:
    value = request.headers.get(header)
    header_debug[f'header_{header}'] = bool(value)
    if value:
      header_debug[f'preview_{header}'] = value[:50] + '...'

  return {
    'has_x_forwarded_access_token': bool(request.headers.get('x-forwarded-access-token')),
    'token_preview': request.headers.get('x-forwarded-access-token', '')[:50] + '...'
    if request.headers.get('x-forwarded-access-token')
    else None,
    'all_headers_debug': header_debug,
    'all_headers_keys': list(request.headers.keys()),
    'middleware_username': getattr(request.state, 'db_auth_username', None),
    'middleware_is_obo': getattr(request.state, 'db_auth_is_obo', False),
    'middleware_has_token': getattr(request.state, 'db_auth_has_token', False),
    'middleware_user_info': getattr(request.state, 'db_auth_user_info', None),
  }


@router.get('/me/workspace', response_model=UserWorkspaceInfo)
def get_user_workspace_info():
  """Get user information along with workspace details."""
  try:
    info = user_utils.get_user_workspace_info()
    return UserWorkspaceInfo(
      user=UserInfo(
        userName=info['user']['userName'],
        displayName=info['user']['displayName'],
        active=info['user']['active'],
      ),
      workspace=info['workspace'],
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
