"""Authentication and authorization endpoints."""

from fastapi import APIRouter, HTTPException, Request

from server.middleware.auth import get_username, is_user_developer

router = APIRouter(prefix='/auth', tags=['Authentication'])


@router.get('/user-role')
async def get_current_user_role(request: Request):
  """Get the current user's role and permissions."""
  username = get_username(request)

  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  is_dev = is_user_developer(request)

  return {
    'username': username,
    'role': 'developer' if is_dev else 'sme',
    'is_developer': is_dev,
    'can_access_dev_pages': is_dev,
  }


@router.get('/check-dev-access')
async def check_dev_access(request: Request):
  """Check if current user can access /dev pages."""
  username = get_username(request)

  if not username:
    raise HTTPException(status_code=401, detail='User not authenticated')

  is_dev = is_user_developer(request)

  if not is_dev:
    raise HTTPException(
      status_code=403, detail='Access denied. Developer role required to access /dev pages.'
    )

  return {'message': 'Access granted', 'role': 'developer'}
