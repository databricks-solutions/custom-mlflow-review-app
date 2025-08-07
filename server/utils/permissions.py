"""Permission checking utilities for MLflow experiments and user roles."""

from functools import lru_cache
from typing import Dict, List

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.ml import ExperimentAccessControlResponse, ExperimentPermissionLevel

from server.utils.config import get_config


def _has_edit_permission_in_experiment(
  user: str, acls: List[ExperimentAccessControlResponse]
) -> bool:
  """Returns True if the user has edit permissions for an experiment."""
  for acl in acls:
    if user in (acl.user_name, acl.group_name, acl.service_principal_name):
      for permission in acl.all_permissions:
        if permission.permission_level in (
          ExperimentPermissionLevel.CAN_EDIT,
          ExperimentPermissionLevel.CAN_MANAGE,
        ):
          return True
  return False


@lru_cache(maxsize=128)
def get_experiment_permissions(experiment_id: str) -> List[ExperimentAccessControlResponse]:
  """Get experiment permissions using Databricks SDK.

  Args:
      experiment_id: The MLflow experiment ID

  Returns:
      List of ExperimentAccessControlResponse objects

  Raises:
      Exception: If unable to fetch permissions
  """
  try:
    client = WorkspaceClient()
    permissions = client.experiments.get_permissions(experiment_id=experiment_id)
    return permissions.access_control_list or []
  except Exception as e:
    raise Exception(f'Failed to get experiment permissions: {str(e)}')


def check_user_experiment_access(user_email: str, experiment_id: str) -> bool:
  """Check if user has any access to the experiment.

  Args:
      user_email: User's email address
      experiment_id: The MLflow experiment ID

  Returns:
      True if user has any permission on the experiment
  """
  try:
    acls = get_experiment_permissions(experiment_id)

    # Check if user has any permission level
    for acl in acls:
      if user_email in (acl.user_name, acl.group_name, acl.service_principal_name):
        return True

    return False
  except Exception:
    # If we can't check permissions, assume no access
    return False


def check_user_can_edit_experiment(user_email: str, experiment_id: str) -> bool:
  """Check if user has CAN_EDIT or CAN_MANAGE permissions on experiment.

  Args:
      user_email: User's email address
      experiment_id: The MLflow experiment ID

  Returns:
      True if user can edit the experiment
  """
  try:
    acls = get_experiment_permissions(experiment_id)
    return _has_edit_permission_in_experiment(user_email, acls)
  except Exception:
    # If we can't check permissions, assume no edit access
    return False


def is_developer(user_email: str) -> bool:
  """Check if user is a developer based on config.yaml.

  Args:
      user_email: User's email address

  Returns:
      True if user is in the developers list
  """
  try:
    config = get_config()
    developers = config.developers
    return user_email in developers
  except Exception:
    # If we can't read config, assume not a developer
    return False


def check_labeling_session_access(user_email: str, assigned_users: List[str]) -> bool:
  """Check if user can access a labeling session.

  Args:
      user_email: User's email address
      assigned_users: List of users assigned to the labeling session

  Returns:
      True if user is a developer OR is assigned to the session
  """
  # Developers can access all sessions
  if is_developer(user_email):
    return True

  # SMEs can only access sessions they're assigned to
  return user_email in assigned_users


def check_sme_assessment_permission(
  user_email: str, experiment_id: str, assigned_users: List[str]
) -> Dict[str, bool]:
  """Check if SME can add assessments to a labeling session.

  Args:
      user_email: User's email address
      experiment_id: The MLflow experiment ID
      assigned_users: List of users assigned to the labeling session

  Returns:
      Dictionary with permission status and reasons
  """
  result = {
    'can_assess': False,
    'is_developer': False,
    'is_assigned': False,
    'has_edit_permission': False,
    'reason': '',
  }

  # Check if user is a developer
  result['is_developer'] = is_developer(user_email)

  # Check if user is assigned to session
  result['is_assigned'] = user_email in assigned_users

  # Check if user has edit permissions on experiment
  result['has_edit_permission'] = check_user_can_edit_experiment(user_email, experiment_id)

  # Determine if user can assess
  if result['is_developer']:
    result['can_assess'] = True
    result['reason'] = 'Developer access'
  elif result['is_assigned'] and result['has_edit_permission']:
    result['can_assess'] = True
    result['reason'] = 'Assigned SME with edit permissions'
  elif not result['is_assigned']:
    result['reason'] = 'User not assigned to this labeling session'
  elif not result['has_edit_permission']:
    result['reason'] = 'User lacks CAN_EDIT permissions on experiment'
  else:
    result['reason'] = 'Access denied'

  return result


def get_user_role(user_email: str) -> str:
  """Get user role (developer or sme).

  Args:
      user_email: User's email address

  Returns:
      'developer' if user is in developers list, 'sme' otherwise
  """
  return 'developer' if is_developer(user_email) else 'sme'
