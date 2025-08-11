"""Unified manifest endpoint that returns all application state."""

import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from server.middleware import get_obo_user_info, has_user_token, is_obo_request
from server.middleware.auth import get_username, is_user_developer
from server.models.review_apps import ReviewApp
from server.utils.config import config
from server.utils.review_apps_utils import review_apps_utils
from server.utils.user_utils import user_utils


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


class WorkspaceInfo(BaseModel):
  """Workspace information."""

  url: str
  deployment_name: str


class ConfigInfo(BaseModel):
  """Application configuration."""

  experiment_id: str | None
  review_app_id: str | None  # The review app ID for the experiment
  max_results: int
  page_size: int
  debug: bool


class AppManifest(BaseModel):
  """Complete application manifest with all necessary information."""

  user: UserInfo
  workspace: WorkspaceInfo
  config: ConfigInfo
  review_app: ReviewApp | None = None


router = APIRouter()


@router.get('/manifest', response_model=AppManifest)
async def get_app_manifest(request: Request):
  """Get complete application manifest including user, workspace, and config."""
  try:
    # Check for test override email
    test_obo_email = os.getenv('TEST_OBO_EMAIL')
    
    # Get user information
    is_obo = is_obo_request(request)
    obo_user_info = get_obo_user_info(request)

    # Get role information
    username = get_username(request)
    is_dev = is_user_developer(request)
    user_role = 'developer' if is_dev else 'sme'

    # Debug: Check if we have the x-forwarded-access-token header
    has_forwarded_token = bool(request.headers.get('x-forwarded-access-token'))

    # Build user info with test override if defined
    if test_obo_email:
      # Use test override email
      user_info = UserInfo(
        userName=test_obo_email,
        displayName=test_obo_email.split('@')[0].replace('.', ' ').title(),
        active=True,
        emails=[test_obo_email],
        # Auth middleware properties
        is_obo=True,
        has_token=True,
        # Role and permissions (test user gets developer access)
        role='developer',
        is_developer=True,
        can_access_dev_pages=True,
      )
    elif is_obo and obo_user_info:
      user_info = UserInfo(
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
      databricks_user_info = user_utils.get_current_user()
      user_info = UserInfo(
        userName=databricks_user_info['userName'],
        displayName=databricks_user_info['displayName'],
        active=databricks_user_info['active'],
        emails=databricks_user_info['emails'],
        # Auth middleware properties
        is_obo=has_forwarded_token,
        has_token=has_user_token(request),
        # Role and permissions
        role=user_role,
        is_developer=is_dev,
        can_access_dev_pages=is_dev,
      )

    # Get workspace information
    workspace_data = user_utils.get_user_workspace_info()
    workspace_info = WorkspaceInfo(
      url=workspace_data['workspace']['url'],
      deployment_name=workspace_data['workspace']['deployment_name'],
    )

    # Get review app data if experiment is configured
    review_app_id = None
    review_app_data = None
    if config.experiment_id:
      try:
        review_app_data = await review_apps_utils.get_review_app_by_experiment(config.experiment_id)
        if review_app_data:
          review_app_id = review_app_data.get('review_app_id')
      except Exception:
        # Silently fail if review app not found
        pass

    # Get configuration
    config_info = ConfigInfo(
      experiment_id=config.experiment_id,
      review_app_id=review_app_id,
      max_results=config.max_results,
      page_size=config.page_size,
      debug=config.debug,
    )

    return AppManifest(
      user=user_info,
      workspace=workspace_info,
      config=config_info,
      review_app=review_app_data,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
