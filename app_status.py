#!/usr/bin/env python3
"""Databricks App Status Checker.

Retrieves and validates Databricks app status, OBO configuration, and experiment permissions.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv


def load_env_local():
  """Load environment variables from .env.local file."""
  env_file = Path('.env.local')
  if not env_file.exists():
    return {}

  env_vars = {}
  with open(env_file) as f:
    for line in f:
      line = line.strip()
      if line and not line.startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        env_vars[key] = value
        # Also set in os.environ for subprocess calls
        os.environ[key] = value

  return env_vars


def load_config_yaml() -> Dict[str, Any]:
  """Load configuration from environment variables."""
  import os

  # Load from environment
  load_dotenv('.env')
  load_dotenv('.env.local')

  # Get values from environment
  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')
  if experiment_id:
    return {'mlflow': {'experiment_id': experiment_id}}

  return {}


def run_databricks_command(cmd: list, profile: Optional[str] = None) -> Tuple[bool, str]:
  """Run a databricks CLI command and return success status and output."""
  full_cmd = ['databricks'] + cmd
  if profile:
    full_cmd.extend(['--profile', profile])

  try:
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
  except subprocess.TimeoutExpired:
    return False, 'Command timed out'
  except Exception as e:
    return False, f'Command failed: {e}'


def get_workspace_obo_status(
  auth_type: str, profile: Optional[str] = None, app_status: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  """Get workspace OBO (On-Behalf-Of) status from preview settings using Databricks SDK."""
  try:
    from databricks.sdk import WorkspaceClient

    # Create workspace client - it should use the same auth as our CLI commands
    if auth_type == 'profile' and profile:
      # Use profile-based auth
      w = WorkspaceClient(profile=profile)
    else:
      # Use environment-based auth (PAT token)
      w = WorkspaceClient()

    # Get workspace ID
    workspace_id = str(w.get_workspace_id())

    # Get workspace preview settings using API client directly
    # Use the workspace client's api_client for consistency
    settings_path = f'/api/2.0/settings-preview/list/workspace/{workspace_id}'

    response = w.api_client.do('GET', settings_path)
    settings_data = response

    # The API returns preview_data_binding with a list of settings
    settings_list = settings_data.get('preview_data_binding', [])

    # Look for OBO-related settings
    obo_enabled = False
    obo_setting = None

    for setting in settings_list:
      setting_name = setting.get('setting_name', '')
      preview_name = setting.get('preview_name', '')

      # Look for OBO-related settings - specifically the apps OBO setting
      if (
        setting_name == 'enable_obo_user_apps'
        or preview_name == 'enable_obo_user_apps'
        or 'obo_user_apps' in setting_name
        or 'behalf' in setting_name.lower()
      ):
        # Check if the setting is enabled
        if setting.get('is_enabled', False):
          obo_enabled = True
          obo_setting = setting
          break

    return {
      'workspace_id': workspace_id,
      'obo_enabled': obo_enabled,
      'obo_setting': obo_setting,
      'all_settings_count': len(settings_list),
    }

  except ImportError:
    return {'error': 'databricks-sdk not available, falling back to CLI method'}
  except Exception as e:
    return {'error': f'Failed to get workspace OBO status via SDK: {str(e)}'}


def get_app_status(app_name: str, auth_type: str, profile: Optional[str] = None) -> Dict[str, Any]:
  """Get Databricks app status information."""
  cmd = ['apps', 'get', app_name, '--output', 'json']
  success, output = run_databricks_command(cmd, profile if auth_type == 'profile' else None)

  if not success:
    return {'error': f'Failed to get app status: {output}', 'app_name': app_name}

  try:
    return json.loads(output)
  except json.JSONDecodeError as e:
    return {
      'error': f'Failed to parse app status JSON: {e}',
      'app_name': app_name,
      'raw_output': output,
    }


def get_experiment_permissions(
  experiment_id: str, auth_type: str, profile: Optional[str] = None
) -> Dict[str, Any]:
  """Get MLflow experiment permissions."""
  cmd = ['api', 'get', f'/api/2.0/permissions/experiments/{experiment_id}']
  success, output = run_databricks_command(cmd, profile if auth_type == 'profile' else None)

  if not success:
    return {
      'error': f'Failed to get experiment permissions: {output}',
      'experiment_id': experiment_id,
    }

  try:
    return json.loads(output)
  except json.JSONDecodeError as e:
    return {
      'error': f'Failed to parse experiment permissions JSON: {e}',
      'experiment_id': experiment_id,
      'raw_output': output,
    }


def check_user_authorization_sp_permissions(
  permissions_data: Dict[str, Any], app_status: Dict[str, Any]
) -> Dict[str, Any]:
  """Check if the app's service principals have permissions for OBO functionality."""
  if 'error' in permissions_data:
    return permissions_data

  access_control_list = permissions_data.get('access_control_list', [])

  # Get the service principal name from app status (should be like app-xxx-name)
  service_principal_name = app_status.get('service_principal_name', '')

  permissions_summary = []
  service_sp_found = False
  service_sp_permissions = []

  for acl in access_control_list:
    principal = (
      acl.get('service_principal_name')
      or acl.get('user_name')
      or acl.get('group_name')
      or 'Unknown'
    )
    permissions = acl.get('all_permissions', [])
    permission_levels = [p.get('permission_level', 'Unknown') for p in permissions]

    permissions_summary.append(
      {
        'principal': principal,
        'type': 'service_principal'
        if acl.get('service_principal_name')
        else ('user' if acl.get('user_name') else 'group'),
        'permissions': permission_levels,
      }
    )

    # Check for the app service principal
    if acl.get('service_principal_name') == service_principal_name:
      service_sp_found = True
      service_sp_permissions = permission_levels

  return {
    'permissions_summary': permissions_summary,
    'primary_service_principal': {
      'id': service_principal_name,
      'found': service_sp_found,
      'permissions': service_sp_permissions,
      'type': 'service_principal',
    },
    'experiment_id': permissions_data.get('object_id', '').replace('/experiments/', ''),
    'total_principals': len(permissions_summary),
  }


def format_text_output(data: Dict[str, Any]) -> str:
  """Format the data as human-readable text."""
  lines = []

  # Header
  lines.append('🔍 Databricks App Status Report')
  lines.append('=' * 50)
  lines.append('')

  # App basic info
  if 'error' in data:
    lines.append(f'❌ Error: {data["error"]}')
    return '\n'.join(lines)

  app_info = data.get('app_status', {})
  lines.append(f'📱 App Name: {data.get("app_name", "Unknown")}')
  lines.append(f'🌐 App URL: {app_info.get("url", "Not available")}')
  lines.append(f'👤 Service Principal: {app_info.get("service_principal_name", "Not available")}')
  oauth2_client_id = app_info.get('oauth2_app_client_id', 'Not available')
  lines.append(f'🔑 User Authorization Service Principal: {oauth2_client_id}')

  # Get actual OBO status from workspace settings
  workspace_obo_data = data.get('workspace_obo_status', {})
  if 'error' in workspace_obo_data:
    obo_status_text = f'UNKNOWN ({workspace_obo_data["error"]})'
    obo_emoji = '⚠️'
  else:
    obo_enabled = workspace_obo_data.get('obo_enabled', False)
    obo_status_text = 'ENABLED' if obo_enabled else 'DISABLED'
    obo_emoji = '✅' if obo_enabled else '❌'

  lines.append(f'{obo_emoji} OBO (On-Behalf-Of): {obo_status_text}')
  lines.append('')

  # App status
  app_status = app_info.get('app_status', {})
  app_state = app_status.get('state', 'Unknown')
  if app_state == 'RUNNING':
    app_emoji = '✅'
  elif app_state == 'UNAVAILABLE':
    app_emoji = '❌'
  elif app_state == 'STARTING':
    app_emoji = '⏳'
  else:
    app_emoji = '❓'
  lines.append(f'{app_emoji} App Status: {app_state}')
  lines.append(f'   Message: {app_status.get("message", "No message")}')
  lines.append('')

  # Compute status
  compute_status = app_info.get('compute_status', {})
  compute_state = compute_status.get('state', 'Unknown')
  if compute_state == 'ACTIVE':
    compute_emoji = '✅'
  elif compute_state == 'INACTIVE':
    compute_emoji = '❌'
  elif compute_state == 'STARTING':
    compute_emoji = '⏳'
  else:
    compute_emoji = '❓'
  lines.append(f'{compute_emoji} Compute Status: {compute_state}')
  lines.append(f'   Message: {compute_status.get("message", "No message")}')
  lines.append('')

  # Experiment permissions
  exp_check = data.get('experiment_permissions', {})
  if 'error' in exp_check:
    lines.append(f'⚠️  Experiment Permission Check: {exp_check["error"]}')
  else:
    lines.append(
      f'🔬 MLflow Experiment Permissions (ID: {exp_check.get("experiment_id", "Unknown")}):'
    )
    lines.append('🔐 Current Permissions:')

    for perm in exp_check.get('permissions_summary', []):
      principal = perm['principal']
      permissions = ', '.join(perm['permissions'])
      lines.append(f'   👤 {principal}: {permissions}')

    lines.append('')

    # Service principal status for OBO
    primary_sp = exp_check.get('primary_service_principal', {})
    oauth2_sp = exp_check.get('oauth2_app_client', {})
    service_sp = exp_check.get('service_principal_client', {})

    lines.append('🔑 OBO Service Principal Status:')

    # Show Service Principal Client ID status
    if service_sp.get('id'):
      sp_id = service_sp.get('id')
      sp_found = service_sp.get('found', False)
      sp_permissions = service_sp.get('permissions', [])

      if sp_found:
        permissions_str = ', '.join(sp_permissions)
        lines.append(f'   ✅ Service Principal Client ({sp_id}): {permissions_str}')
      else:
        lines.append(f'   ❌ Service Principal Client ({sp_id}): NOT found')

    # Show OAuth2 App Client ID status
    if oauth2_sp.get('id'):
      oauth_id = oauth2_sp.get('id')
      oauth_found = oauth2_sp.get('found', False)
      oauth_permissions = oauth2_sp.get('permissions', [])

      if oauth_found:
        permissions_str = ', '.join(oauth_permissions)
        lines.append(f'   ✅ OAuth2 App Client ({oauth_id}): {permissions_str}')
      else:
        lines.append(f'   ❌ OAuth2 App Client ({oauth_id}): NOT found')

    # Overall status
    primary_found = primary_sp.get('found', False)

    if primary_found:
      permissions_str = ', '.join(primary_sp.get('permissions', []))
      lines.append(f'   ✅ Primary OBO Service Principal has permissions: {permissions_str}')
    else:
      lines.append('   ❌ No OBO service principal permissions found')
      lines.append('   💡 Run setup.sh to configure OBO permissions automatically')

  lines.append('')
  lines.append('💡 Useful commands:')
  lines.append('   View app logs: Visit app URL + /logz in browser')
  lines.append('   Deploy app: ./deploy.sh')
  lines.append('   Update config: ./setup.sh')
  lines.append('   Check status: uv run python app_status.py')
  lines.append('   Get JSON output: uv run python app_status.py --format json')
  lines.append('')
  lines.append('⚠️  IMPORTANT: After enabling OBO in workspace settings,')
  lines.append('   you must restart your Databricks App for changes to take effect!')

  return '\n'.join(lines)


def main():
  """Main function to handle command line arguments and orchestrate the status check."""
  parser = argparse.ArgumentParser(description='Check Databricks App status and permissions')
  parser.add_argument(
    '--format', choices=['text', 'json'], default='text', help='Output format (default: text)'
  )
  parser.add_argument('--app-name', help='Override app name from environment')
  parser.add_argument('--experiment-id', help='Override experiment ID from config.yaml')
  parser.add_argument('--verbose', action='store_true', help='Include additional details')

  args = parser.parse_args()

  # Load environment and config
  env_vars = load_env_local()
  config = load_config_yaml()

  # Get app name
  app_name = args.app_name or env_vars.get('DATABRICKS_APP_NAME')
  if not app_name:
    error_data = {'error': 'DATABRICKS_APP_NAME not found. Please run ./setup.sh first.'}
    if args.format == 'json':
      print(json.dumps(error_data, indent=2))
    else:
      print('❌ DATABRICKS_APP_NAME not found. Please run ./setup.sh first.')
    sys.exit(1)

  # Get auth configuration
  auth_type = env_vars.get('DATABRICKS_AUTH_TYPE')
  if not auth_type:
    error_data = {'error': 'DATABRICKS_AUTH_TYPE not found. Please run ./setup.sh first.'}
    if args.format == 'json':
      print(json.dumps(error_data, indent=2))
    else:
      print('❌ DATABRICKS_AUTH_TYPE not found. Please run ./setup.sh first.')
    sys.exit(1)

  profile = env_vars.get('DATABRICKS_CONFIG_PROFILE') if auth_type == 'profile' else None

  # Get app status
  app_status = get_app_status(app_name, auth_type, profile)

  # Get workspace OBO status
  workspace_obo_status = get_workspace_obo_status(auth_type, profile, app_status)

  # Prepare result data
  result_data = {
    'app_name': app_name,
    'app_status': app_status,
    'workspace_obo_status': workspace_obo_status,
  }

  # Get experiment permissions if app status is successful
  if 'error' not in app_status:
    experiment_id = args.experiment_id or config.get('mlflow', {}).get('experiment_id')

    if experiment_id:
      permissions_data = get_experiment_permissions(experiment_id, auth_type, profile)
      result_data['experiment_permissions'] = check_user_authorization_sp_permissions(
        permissions_data, app_status
      )
    elif not experiment_id:
      result_data['experiment_permissions'] = {
        'error': 'No experiment_id found in config.yaml. Run ./setup.sh to configure.'
      }

  # Output results
  if args.format == 'json':
    print(json.dumps(result_data, indent=2))
  else:
    print(format_text_output(result_data))

  # Exit with error code if there are any errors
  has_errors = 'error' in result_data.get('app_status', {}) or 'error' in result_data.get(
    'experiment_permissions', {}
  )

  sys.exit(1 if has_errors else 0)


if __name__ == '__main__':
  main()
