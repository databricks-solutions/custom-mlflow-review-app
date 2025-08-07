#!/usr/bin/env python3
"""Check and verify permissions for MLflow experiment and Databricks App.

This script performs sanity checks to ensure:
1. The app's service principal has CAN_MANAGE permission on the experiment
2. All developers in config.yaml have CAN_MANAGE permission on the experiment
3. The current user has CAN_MANAGE permission on the experiment

Usage:
    uv run python check_permissions.py
    uv run python check_permissions.py --fix  # Automatically grant missing permissions
    uv run python check_permissions.py --json  # Output in JSON format
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Import functions from existing modules
from app_status import get_app_status, get_experiment_permissions, load_env_local


def load_config_yaml() -> Dict[str, Any]:
  """Load configuration from environment variables."""
  import os

  # Load from environment
  load_dotenv('.env')
  load_dotenv('.env.local')

  # Get values from environment
  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')
  developers_str = os.getenv('DEVELOPERS', '')
  developers = (
    [dev.strip() for dev in developers_str.split(',') if dev.strip()] if developers_str else []
  )

  config = {}
  if experiment_id:
    config['mlflow'] = {'experiment_id': experiment_id}
  if developers:
    config['developers'] = developers

  return config


def get_current_user_email(auth_type: str, profile: Optional[str] = None) -> Optional[str]:
  """Get current user email from Databricks."""
  try:
    from databricks.sdk import WorkspaceClient

    if auth_type == 'profile' and profile:
      w = WorkspaceClient(profile=profile)
    else:
      w = WorkspaceClient()

    current_user = w.current_user.me()
    return current_user.user_name if current_user else None

  except Exception:
    return None


def check_permissions(
  experiment_id: str,
  auth_type: str,
  profile: Optional[str] = None,
  app_name: Optional[str] = None,
) -> Dict[str, Any]:
  """Check permissions for all required principals."""
  result = {
    'experiment_id': experiment_id,
    'status': 'OK',
    'issues': [],
    'permissions': {},
    'summary': {},
  }

  # Get experiment permissions
  permissions_data = get_experiment_permissions(experiment_id, auth_type, profile)

  if 'error' in permissions_data:
    result['status'] = 'ERROR'
    result['error'] = f'Failed to get experiment permissions: {permissions_data["error"]}'
    return result

  # Parse permissions
  access_control_list = permissions_data.get('access_control_list', [])
  current_permissions = {}

  for acl in access_control_list:
    principal = acl.get('service_principal_name') or acl.get('user_name') or acl.get('group_name')
    if principal:
      permissions = acl.get('all_permissions', [])
      permission_levels = [p.get('permission_level', 'Unknown') for p in permissions]
      current_permissions[principal] = {
        'type': 'service_principal'
        if acl.get('service_principal_name')
        else ('user' if acl.get('user_name') else 'group'),
        'permissions': permission_levels,
        'has_can_manage': 'CAN_MANAGE' in permission_levels,
      }

  result['permissions'] = current_permissions

  # Check app service principal
  if app_name:
    app_status = get_app_status(app_name, auth_type, profile)
    if 'error' not in app_status:
      service_principal_name = app_status.get('service_principal_name', '')
      service_principal_id = app_status.get(
        'service_principal_client_id', ''
      )  # UUID used in permissions API
      if service_principal_name:
        # Check by both name and UUID since permissions might list the UUID
        sp_info = current_permissions.get(service_principal_name, {})
        if not sp_info and service_principal_id:
          sp_info = current_permissions.get(service_principal_id, {})
        has_manage = sp_info.get('has_can_manage', False)

        result['summary']['app_service_principal'] = {
          'name': service_principal_name,
          'id': service_principal_id,  # Store UUID for grant operations
          'has_can_manage': has_manage,
          'permissions': sp_info.get('permissions', []),
        }

        if not has_manage:
          result['status'] = 'MISSING_PERMISSIONS'
          result['issues'].append(
            f'App service principal {service_principal_name} is missing CAN_MANAGE permission'
          )
      else:
        result['issues'].append('Could not determine app service principal')
    else:
      result['issues'].append(f'Could not get app status: {app_status.get("error")}')

  # Check current user
  current_user = get_current_user_email(auth_type, profile)
  if current_user:
    user_info = current_permissions.get(current_user, {})
    has_manage = user_info.get('has_can_manage', False)

    result['summary']['current_user'] = {
      'email': current_user,
      'has_can_manage': has_manage,
      'permissions': user_info.get('permissions', []),
    }

    if not has_manage:
      result['status'] = 'MISSING_PERMISSIONS'
      result['issues'].append(f'Current user {current_user} is missing CAN_MANAGE permission')
  else:
    result['issues'].append('Could not determine current user')

  # Check developers from config.yaml
  config = load_config_yaml()
  developers = config.get('developers', [])
  developers_summary = []

  for dev_email in developers:
    dev_info = current_permissions.get(dev_email, {})
    has_manage = dev_info.get('has_can_manage', False)

    developers_summary.append(
      {
        'email': dev_email,
        'has_can_manage': has_manage,
        'permissions': dev_info.get('permissions', []),
      }
    )

    if not has_manage:
      result['status'] = 'MISSING_PERMISSIONS'
      result['issues'].append(f'Developer {dev_email} is missing CAN_MANAGE permission')

  result['summary']['developers'] = developers_summary

  # Count statistics
  can_manage_users = sum(
    1 for p in current_permissions.values() if p['type'] == 'user' and p['has_can_manage']
  )
  can_manage_sps = sum(
    1
    for p in current_permissions.values()
    if p['type'] == 'service_principal' and p['has_can_manage']
  )

  result['summary']['statistics'] = {
    'total_principals': len(current_permissions),
    'users_with_can_manage': can_manage_users,
    'service_principals_with_can_manage': can_manage_sps,
  }

  return result


def grant_permission(
  experiment_id: str,
  principal_type: str,
  principal_id: str,
  permission: str = 'CAN_MANAGE',
) -> bool:
  """Grant permission to a principal using the grant_experiment_permissions tool."""
  import subprocess

  try:
    cmd = [
      'uv',
      'run',
      'python',
      'tools/grant_experiment_permissions.py',
      '--experiment-id',
      experiment_id,
      '--principal-type',
      principal_type,
      '--principal-id',
      principal_id,
      '--permission',
      permission,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0

  except Exception:
    return False


def fix_permissions(
  check_result: Dict[str, Any], experiment_id: str, interactive: bool = True
) -> Dict[str, Any]:
  """Fix missing permissions identified in check_result."""
  fix_result = {'fixed': [], 'failed': []}

  if check_result['status'] != 'MISSING_PERMISSIONS':
    fix_result['message'] = 'No permissions to fix'
    return fix_result

  # Collect principals needing permissions
  to_fix = []

  # App service principal
  app_sp = check_result['summary'].get('app_service_principal', {})
  if app_sp and not app_sp.get('has_can_manage'):
    # Use service_principal_client_id (UUID) for API calls
    sp_id = app_sp.get('id')  # This should be the service_principal_client_id
    if sp_id:
      to_fix.append(('service_principal', sp_id, 'App Service Principal'))
    else:
      print('⚠️ Could not determine service principal UUID, skipping app SP...')

  # Current user
  current_user = check_result['summary'].get('current_user', {})
  if current_user and not current_user.get('has_can_manage'):
    to_fix.append(('user', current_user['email'], 'Current User'))

  # Developers
  for dev in check_result['summary'].get('developers', []):
    if not dev.get('has_can_manage'):
      to_fix.append(('user', dev['email'], 'Developer'))

  if not to_fix:
    fix_result['message'] = 'No principals need permission grants'
    return fix_result

  # Grant permissions
  if interactive:
    print(f'\n🔧 Need to grant CAN_MANAGE permissions to {len(to_fix)} principal(s):')
    for principal_type, principal_id, description in to_fix:
      print(f'   • {principal_id} ({description})')

    confirm = input('\nProceed with granting permissions? [y/N]: ')
    if confirm.lower() != 'y':
      fix_result['message'] = 'Permission granting cancelled by user'
      return fix_result

  print('\nGranting permissions...')
  for principal_type, principal_id, description in to_fix:
    if grant_permission(experiment_id, principal_type, principal_id):
      print(f'✅ Granted CAN_MANAGE to {principal_id}')
      fix_result['fixed'].append(principal_id)
    else:
      print(f'❌ Failed to grant permission to {principal_id}')
      fix_result['failed'].append(principal_id)

  return fix_result


def format_text_output(check_result: Dict[str, Any]) -> str:
  """Format the check result as human-readable text."""
  lines = []

  lines.append('🔍 MLflow Experiment Permissions Check')
  lines.append('=' * 40)
  lines.append(f'Experiment ID: {check_result["experiment_id"]}')
  lines.append('')

  if check_result.get('error'):
    lines.append(f'❌ Error: {check_result["error"]}')
    return '\n'.join(lines)

  # Display all permissions inline
  lines.append('🔐 CURRENT PERMISSIONS')
  lines.append('=' * 20)

  # Get app SP, developers, and current user for highlighting
  app_sp = check_result['summary'].get('app_service_principal')
  developers = check_result['summary'].get('developers', [])
  dev_emails = [dev['email'] for dev in developers]
  app_sp_id = app_sp.get('id') if app_sp else None
  app_sp_name = app_sp.get('name') if app_sp else None

  # Display all permissions from the permissions dict
  permissions = check_result.get('permissions', {})
  for principal, info in permissions.items():
    principal_type = info['type'].replace('_', ' ').title()
    permissions_str = ', '.join(info['permissions'])

    # Check if this is the app service principal or a developer
    if app_sp_id and principal == app_sp_id:
      # Show app service principal with star prefix
      lines.append(f'  ⭐ {app_sp_name} ({principal_type}): {permissions_str}')
    elif info['type'] == 'user' and principal in dev_emails:
      # Show developers with wrench prefix
      lines.append(f'  🔧 {principal} (User): {permissions_str}')
    else:
      lines.append(f'  • {principal} ({principal_type}): {permissions_str}')

  lines.append('')

  # Status summary
  status = check_result['status']
  if status == 'OK':
    lines.append('✅ STATUS: All permissions are correctly configured')
  elif status == 'MISSING_PERMISSIONS':
    lines.append('❌ STATUS: Some principals are missing required permissions')
    lines.append('')

    # Show what's missing
    if app_sp and not app_sp.get('has_can_manage'):
      lines.append(f'  ❌ App service principal {app_sp["name"]} needs CAN_MANAGE')

    current_user = check_result['summary'].get('current_user')
    if current_user and not current_user.get('has_can_manage'):
      lines.append(f'  ❌ Current user {current_user["email"]} needs CAN_MANAGE')

    for dev in developers:
      if not dev.get('has_can_manage'):
        lines.append(f'  ❌ Developer {dev["email"]} needs CAN_MANAGE')

    lines.append('')
    lines.append('💡 Run with --fix flag to automatically grant missing permissions')
  else:
    lines.append(f'❌ STATUS: {status}')

  lines.append('')

  # Statistics
  stats = check_result['summary'].get('statistics', {})
  if stats:
    lines.append('📊 STATISTICS')
    lines.append('-' * 13)
    lines.append(f'Total principals: {stats["total_principals"]}')
    lines.append(f'Users with CAN_MANAGE: {stats["users_with_can_manage"]}')
    lines.append(
      f'Service Principals with CAN_MANAGE: {stats["service_principals_with_can_manage"]}'
    )

  return '\n'.join(lines)


def main():
  """Main function to check permissions."""
  parser = argparse.ArgumentParser(
    description='Check MLflow experiment permissions for app and developers'
  )
  parser.add_argument(
    '--fix',
    action='store_true',
    help='Automatically grant missing permissions',
  )
  parser.add_argument(
    '--json',
    action='store_true',
    help='Output results in JSON format',
  )
  parser.add_argument(
    '--experiment-id',
    help='Override experiment ID from config.yaml',
  )
  parser.add_argument(
    '--app-name',
    help='Override app name from environment',
  )

  args = parser.parse_args()

  # Load configuration
  env_vars = load_env_local()
  config = load_config_yaml()

  # Get parameters
  experiment_id = args.experiment_id or config.get('mlflow', {}).get('experiment_id')
  app_name = args.app_name or env_vars.get('DATABRICKS_APP_NAME')
  auth_type = env_vars.get('DATABRICKS_AUTH_TYPE')
  profile = env_vars.get('DATABRICKS_CONFIG_PROFILE') if auth_type == 'profile' else None

  # Validate
  if not experiment_id:
    error = {'error': 'No experiment_id found in config.yaml or --experiment-id'}
    if args.json:
      print(json.dumps(error, indent=2))
    else:
      print('❌ No experiment_id found in config.yaml')
      print('   Run ./setup.sh to configure or use --experiment-id flag')
    sys.exit(1)

  if not auth_type:
    error = {'error': 'DATABRICKS_AUTH_TYPE not found in .env.local'}
    if args.json:
      print(json.dumps(error, indent=2))
    else:
      print('❌ DATABRICKS_AUTH_TYPE not found in .env.local')
      print('   Run ./setup.sh to configure authentication')
    sys.exit(1)

  # Check permissions
  check_result = check_permissions(experiment_id, auth_type, profile, app_name)

  # Fix if requested
  if args.fix and check_result['status'] == 'MISSING_PERMISSIONS':
    fix_result = fix_permissions(check_result, experiment_id, interactive=not args.json)
    check_result['fix_result'] = fix_result

    # Re-check after fixing
    if fix_result.get('fixed'):
      print('\n🔍 Re-checking permissions after fixes...')
      check_result = check_permissions(experiment_id, auth_type, profile, app_name)

  # Output results
  if args.json:
    print(json.dumps(check_result, indent=2))
  else:
    print(format_text_output(check_result))

  # Exit code based on status
  if check_result['status'] == 'OK':
    sys.exit(0)
  else:
    sys.exit(1)


if __name__ == '__main__':
  main()
