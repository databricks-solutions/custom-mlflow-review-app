"""Permission checking utilities for MLflow experiments and user roles."""

import json
import subprocess
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.ml import ExperimentAccessControlResponse, ExperimentPermissionLevel
from pydantic import BaseModel

from server.utils.config import get_config


# Pydantic models for permissions
class PermissionInfo(BaseModel):
  """Single permission entry."""
  permission_level: str
  inherited: bool = False


class AccessControlEntry(BaseModel):
  """Access control entry for experiment permissions."""
  user_name: Optional[str] = None
  group_name: Optional[str] = None
  service_principal_name: Optional[str] = None
  all_permissions: List[PermissionInfo] = []


def is_notebook_experiment(experiment_id: str) -> bool:
  """Check if experiment is notebook-style by checking tags.
  
  Args:
      experiment_id: The MLflow experiment ID
      
  Returns:
      True if experiment has experimentType == "NOTEBOOK" tag
  """
  try:
    # Set tracking URI to Databricks if needed
    if mlflow.get_tracking_uri() != 'databricks':
      mlflow.set_tracking_uri('databricks')
    
    experiment = mlflow.get_experiment(experiment_id)
    if experiment and experiment.tags:
      return experiment.tags.get('mlflow.experimentType') == 'NOTEBOOK'
    return False
  except Exception:
    # If we can't determine type, assume regular experiment
    return False


def get_permissions_api_endpoint(experiment_id: str, is_notebook: bool) -> str:
  """Get correct API endpoint based on experiment type.
  
  Args:
      experiment_id: The MLflow experiment ID
      is_notebook: Whether the experiment is notebook-style
      
  Returns:
      API endpoint path for permissions
  """
  if is_notebook:
    return f'/api/2.0/preview/permissions/notebooks/{experiment_id}'
  else:
    return f'/api/2.0/permissions/experiments/{experiment_id}'


def run_databricks_command(cmd: List[str]) -> Tuple[bool, str]:
  """Run a databricks CLI command and return success status and output."""
  try:
    result = subprocess.run(['databricks'] + cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
  except subprocess.TimeoutExpired:
    return False, 'Command timed out'
  except Exception as e:
    return False, f'Command failed: {e}'


def transform_extended_permissions(extended_acls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Transform extended permission format to simple format.
  
  Notebook API returns extended format with all_permissions array,
  we need to transform it to match the regular format.
  """
  simple_acls = []
  
  for entry in extended_acls:
    # Build simple ACL entry
    simple_entry = {}
    
    # Copy principal identifiers
    if 'user_name' in entry:
      simple_entry['user_name'] = entry['user_name']
    if 'group_name' in entry:
      simple_entry['group_name'] = entry['group_name']
    if 'service_principal_name' in entry:
      simple_entry['service_principal_name'] = entry['service_principal_name']
    
    # Copy all_permissions if present
    if 'all_permissions' in entry:
      simple_entry['all_permissions'] = entry['all_permissions']
    elif 'permission_level' in entry:
      # If we have a direct permission_level, create all_permissions structure
      simple_entry['all_permissions'] = [
        {'permission_level': entry['permission_level'], 'inherited': False}
      ]
    
    simple_acls.append(simple_entry)
  
  return simple_acls


def get_experiment_permissions_via_api(experiment_id: str) -> Dict[str, Any]:
  """Get experiment permissions using API calls, handling both experiment types.
  
  Args:
      experiment_id: The MLflow experiment ID
      
  Returns:
      Dictionary with access_control_list
  """
  # Detect experiment type
  is_notebook = is_notebook_experiment(experiment_id)
  
  # Get appropriate endpoint
  endpoint = get_permissions_api_endpoint(experiment_id, is_notebook)
  
  # Make API call
  cmd = ['api', 'get', endpoint]
  success, output = run_databricks_command(cmd)
  
  if not success:
    raise Exception(f'Failed to get experiment permissions: {output}')
  
  try:
    result = json.loads(output)
    
    # Transform to consistent format if needed
    if 'access_control_list' in result:
      acl_list = result['access_control_list']
      # Ensure we have a consistent format
      result['access_control_list'] = transform_extended_permissions(acl_list)
    
    return result
  except json.JSONDecodeError as e:
    raise Exception(f'Failed to parse permissions JSON: {e}')


def _has_edit_permission_in_experiment(
  user: str, acls: List[AccessControlEntry]
) -> bool:
  """Returns True if the user has edit permissions for an experiment."""
  for acl in acls:
    if user in (acl.user_name, acl.group_name, acl.service_principal_name):
      for permission in acl.all_permissions:
        if permission.permission_level in ('CAN_EDIT', 'CAN_MANAGE'):
          return True
  return False


def get_experiment_permissions_unified(experiment_id: str) -> List[AccessControlEntry]:
  """Get experiment permissions handling both regular and notebook experiments.
  
  Args:
      experiment_id: The MLflow experiment ID
      
  Returns:
      List of AccessControlEntry objects (Pydantic models)
  """
  try:
    api_result = get_experiment_permissions_via_api(experiment_id)
    
    # Convert to Pydantic models
    acl_list = []
    for entry in api_result.get('access_control_list', []):
      permissions = [
        PermissionInfo(
          permission_level=perm.get('permission_level', ''),
          inherited=perm.get('inherited', False)
        )
        for perm in entry.get('all_permissions', [])
      ]
      
      acl = AccessControlEntry(
        user_name=entry.get('user_name'),
        group_name=entry.get('group_name'),
        service_principal_name=entry.get('service_principal_name'),
        all_permissions=permissions
      )
      acl_list.append(acl)
    
    return acl_list
  except Exception as e:
    raise Exception(f'Failed to get experiment permissions: {str(e)}')


@lru_cache(maxsize=128)
def get_experiment_permissions(experiment_id: str) -> List[AccessControlEntry]:
  """Get experiment permissions for any experiment type.
  
  Handles both regular and notebook-style experiments automatically.

  Args:
      experiment_id: The MLflow experiment ID

  Returns:
      List of AccessControlEntry objects (Pydantic models)

  Raises:
      Exception: If unable to fetch permissions
  """
  try:
    # First try SDK for regular experiments
    client = WorkspaceClient()
    permissions = client.experiments.get_permissions(experiment_id=experiment_id)
    
    # Convert SDK response to our Pydantic models
    acl_list = []
    for sdk_acl in (permissions.access_control_list or []):
      permissions_list = [
        PermissionInfo(
          permission_level=perm.permission_level,
          inherited=getattr(perm, 'inherited', False)
        )
        for perm in (sdk_acl.all_permissions or [])
      ]
      
      acl = AccessControlEntry(
        user_name=sdk_acl.user_name,
        group_name=sdk_acl.group_name,
        service_principal_name=sdk_acl.service_principal_name,
        all_permissions=permissions_list
      )
      acl_list.append(acl)
    
    return acl_list
  except Exception as sdk_error:
    # If SDK fails, check if it's a notebook experiment
    if 'not a experiment' in str(sdk_error).lower() or 'not found' in str(sdk_error).lower():
      try:
        # Get permissions using API call - already returns Pydantic models
        return get_experiment_permissions_unified(experiment_id)
      except Exception as api_error:
        raise Exception(f'Failed to get experiment permissions: SDK error: {str(sdk_error)}, API error: {str(api_error)}')
    else:
      raise Exception(f'Failed to get experiment permissions: {str(sdk_error)}')


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
