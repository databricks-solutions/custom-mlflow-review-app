#!/usr/bin/env python3
"""Grant permissions to a service principal or user for an MLflow experiment.

This tool allows you to programmatically add permissions to MLflow experiments,
which is essential for enabling OBO (On-Behalf-Of) functionality in Databricks Apps.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

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


def run_databricks_command(cmd: list, profile: Optional[str] = None) -> tuple[bool, str]:
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


def get_current_permissions(
  experiment_id: str, auth_type: str, profile: Optional[str] = None
) -> Dict[str, Any]:
  """Get current experiment permissions."""
  cmd = ['api', 'get', f'/api/2.0/permissions/experiments/{experiment_id}']
  success, output = run_databricks_command(cmd, profile if auth_type == 'profile' else None)

  if not success:
    return {'error': f'Failed to get current permissions: {output}'}

  try:
    return json.loads(output)
  except json.JSONDecodeError as e:
    return {'error': f'Failed to parse permissions JSON: {e}'}


def grant_experiment_permission(
  experiment_id: str,
  principal_id: str,
  principal_type: str,
  permission_level: str,
  auth_type: str,
  profile: Optional[str] = None,
) -> Dict[str, Any]:
  """Grant permission to an experiment."""
  # Validate inputs
  valid_principal_types = ['user', 'service_principal', 'group']
  if principal_type not in valid_principal_types:
    return {'error': f'Invalid principal_type. Must be one of: {valid_principal_types}'}

  valid_permission_levels = ['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE']
  if permission_level not in valid_permission_levels:
    return {'error': f'Invalid permission_level. Must be one of: {valid_permission_levels}'}

  # Create access control entry
  if principal_type == 'user':
    principal_field = 'user_name'
  elif principal_type == 'service_principal':
    principal_field = 'service_principal_name'
  else:  # group
    principal_field = 'group_name'

  access_control_entry = {principal_field: principal_id, 'permission_level': permission_level}

  # Prepare the API call
  request_data = {'access_control_list': [access_control_entry]}

  # Make the API call
  cmd = [
    'api',
    'patch',
    f'/api/2.0/permissions/experiments/{experiment_id}',
    '--json',
    json.dumps(request_data),
  ]
  if profile and auth_type == 'profile':
    cmd.extend(['--profile', profile])

  try:
    result = subprocess.run(['databricks'] + cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
      return {
        'success': True,
        'message': f'Successfully granted {permission_level} to {principal_id}',
      }
    else:
      return {'error': f'Failed to grant permission: {result.stderr}'}

  except subprocess.TimeoutExpired:
    return {'error': 'Request timed out'}
  except Exception as e:
    return {'error': f'Request failed: {e}'}


def main():
  """Main function to handle command line arguments and grant permissions."""
  parser = argparse.ArgumentParser(
    description='Grant permissions to a service principal or user for an MLflow experiment',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Grant CAN_EDIT to a service principal (for OBO functionality)
  uv run python tools/grant_experiment_permissions.py \\
    --principal-id 0ea6d486-310f-4c5b-8e09-f73b0f525bf1 \\
    --principal-type service_principal --permission CAN_EDIT

  # Grant CAN_READ to a user
  uv run python tools/grant_experiment_permissions.py \\
    --principal-id user@company.com --principal-type user \\
    --permission CAN_READ --experiment-id 123456789

  # Grant CAN_MANAGE to a group
  uv run python tools/grant_experiment_permissions.py \\
    --principal-id admins --principal-type group --permission CAN_MANAGE
        """,
  )

  parser.add_argument('--experiment-id', help='MLflow experiment ID (default: from config.yaml)')
  parser.add_argument(
    '--principal-id',
    required=True,
    help='Principal ID (email for users, UUID for service principals, name for groups)',
  )
  parser.add_argument(
    '--principal-type',
    required=True,
    choices=['user', 'service_principal', 'group'],
    help='Type of principal to grant permissions to',
  )
  parser.add_argument(
    '--permission',
    required=True,
    choices=['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE'],
    help='Permission level to grant',
  )
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be done without making changes'
  )
  parser.add_argument(
    '--format', choices=['text', 'json'], default='text', help='Output format (default: text)'
  )

  args = parser.parse_args()

  # Load environment and config
  env_vars = load_env_local()
  config = load_config_yaml()

  # Get experiment ID
  experiment_id = args.experiment_id or config.get('mlflow', {}).get('experiment_id')
  if not experiment_id:
    error_msg = 'No experiment_id provided. Use --experiment-id or configure in config.yaml'
    if args.format == 'json':
      print(json.dumps({'error': error_msg}))
    else:
      print(f'❌ {error_msg}')
    sys.exit(1)

  # Get auth configuration
  auth_type = env_vars.get('DATABRICKS_AUTH_TYPE')
  if not auth_type:
    error_msg = 'DATABRICKS_AUTH_TYPE not found. Please run ./setup.sh first.'
    if args.format == 'json':
      print(json.dumps({'error': error_msg}))
    else:
      print(f'❌ {error_msg}')
    sys.exit(1)

  profile = env_vars.get('DATABRICKS_CONFIG_PROFILE') if auth_type == 'profile' else None

  # Show current permissions first
  if args.format == 'text':
    print(f'🔬 Experiment: {experiment_id}')
    print(f'👤 Principal: {args.principal_id} ({args.principal_type})')
    print(f'🔐 Permission: {args.permission}')
    print('')

    if args.dry_run:
      print('🧪 DRY RUN - No changes will be made')
      print('')

  # Get current permissions to show context
  current_perms = get_current_permissions(experiment_id, auth_type, profile)

  if 'error' not in current_perms and args.format == 'text':
    print('📋 Current permissions:')
    access_control_list = current_perms.get('access_control_list', [])

    for acl in access_control_list:
      principal = (
        acl.get('service_principal_name')
        or acl.get('user_name')
        or acl.get('group_name')
        or 'Unknown'
      )
      permissions = acl.get('all_permissions', [])
      permission_levels = [p.get('permission_level', 'Unknown') for p in permissions]
      print(f'   👤 {principal}: {", ".join(permission_levels)}')
    print('')

  # Check if principal already has permissions
  principal_already_exists = False
  if 'error' not in current_perms:
    access_control_list = current_perms.get('access_control_list', [])
    for acl in access_control_list:
      if (
        acl.get('service_principal_name') == args.principal_id
        or acl.get('user_name') == args.principal_id
        or acl.get('group_name') == args.principal_id
      ):
        principal_already_exists = True
        if args.format == 'text':
          print(f'ℹ️  Principal {args.principal_id} already has permissions on this experiment')
        break

  if args.dry_run:
    if args.format == 'json':
      print(
        json.dumps(
          {
            'dry_run': True,
            'experiment_id': experiment_id,
            'principal_id': args.principal_id,
            'principal_type': args.principal_type,
            'permission': args.permission,
            'principal_already_exists': principal_already_exists,
            'action': 'grant_permission',
          }
        )
      )
    else:
      print(f'✅ Would grant {args.permission} to {args.principal_id}')
      if principal_already_exists:
        print('   (This will update existing permissions)')
      else:
        print('   (This will add new permissions)')
    return

  # Grant the permission
  result = grant_experiment_permission(
    experiment_id, args.principal_id, args.principal_type, args.permission, auth_type, profile
  )

  # Output results
  if args.format == 'json':
    output = {
      'experiment_id': experiment_id,
      'principal_id': args.principal_id,
      'principal_type': args.principal_type,
      'permission': args.permission,
      'principal_already_exists': principal_already_exists,
    }
    output.update(result)
    print(json.dumps(output, indent=2))
  else:
    if 'error' in result:
      print(f'❌ {result["error"]}')
      sys.exit(1)
    else:
      print(f'✅ {result["message"]}')
      print('')
      print('💡 Verify with: uv run python app_status.py')

  sys.exit(0 if 'error' not in result else 1)


if __name__ == '__main__':
  main()
