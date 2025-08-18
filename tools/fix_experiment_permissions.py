#!/usr/bin/env python3
"""Fix missing permissions for MLflow experiments.

This tool analyzes experiment permissions and automatically grants missing permissions
to required principals (app service principal, developers, current user).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from databricks.sdk import WorkspaceClient

from server.utils.config import get_config
from server.utils.permissions import get_experiment_permissions


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


def get_current_user_email() -> Optional[str]:
  """Get current user email from Databricks."""
  try:
    w = WorkspaceClient()
    current_user = w.current_user.me()
    return current_user.user_name if current_user else None
  except Exception:
    return None


def get_app_service_principal(app_name: str) -> Optional[Dict[str, str]]:
  """Get app service principal info."""
  try:
    # Run app_status.py to get service principal info
    result = subprocess.run(
      ['uv', 'run', 'python', 'app_status.py', '--format', 'json'],
      capture_output=True,
      text=True,
      timeout=30
    )
    
    if result.returncode == 0:
      status = json.loads(result.stdout)
      app_status_data = status.get('app_status', {})
      
      # Get the service principal UUID (this is what's used for permissions)
      sp_id = app_status_data.get('service_principal_client_id')
      sp_name = app_status_data.get('service_principal_name')
      
      if sp_id:  # We only need the ID, name is optional
        return {'name': sp_name or sp_id, 'id': sp_id}
  except Exception:
    pass
  
  return None


def analyze_permissions(experiment_id: str) -> Dict[str, Any]:
  """Analyze experiment permissions and identify what needs fixing."""
  result = {
    'experiment_id': experiment_id,
    'missing_permissions': [],
    'existing_permissions': {},
  }
  
  try:
    # Get current permissions
    acl_list = get_experiment_permissions(experiment_id)
    
    # Build existing permissions map
    for acl in acl_list:
      principal = acl.user_name or acl.group_name or acl.service_principal_name
      if principal:
        perms = []
        for perm in acl.all_permissions:
          if not perm.inherited:
            perms.append(perm.permission_level)
        
        if perms:
          result['existing_permissions'][principal] = {
            'type': 'user' if acl.user_name else ('group' if acl.group_name else 'service_principal'),
            'permissions': perms,
            'has_can_manage': 'CAN_MANAGE' in perms,
          }
    
    # Check app service principal
    env_vars = load_env_local()
    app_name = env_vars.get('DATABRICKS_APP_NAME')
    if app_name:
      app_sp = get_app_service_principal(app_name)
      if app_sp:
        sp_id = app_sp['id']
        sp_name = app_sp['name']
        
        # Check both ID and name
        sp_perms = result['existing_permissions'].get(sp_id) or result['existing_permissions'].get(sp_name)
        if not sp_perms or not sp_perms.get('has_can_manage'):
          result['missing_permissions'].append({
            'principal_type': 'service_principal',
            'principal_id': sp_id,
            'principal_name': sp_name,
            'permission': 'CAN_MANAGE',
            'reason': 'App service principal needs CAN_MANAGE'
          })
    
    # Check current user
    current_user = get_current_user_email()
    if current_user:
      user_perms = result['existing_permissions'].get(current_user)
      if not user_perms or not user_perms.get('has_can_manage'):
        result['missing_permissions'].append({
          'principal_type': 'user',
          'principal_id': current_user,
          'principal_name': current_user,
          'permission': 'CAN_MANAGE',
          'reason': 'Current user needs CAN_MANAGE'
        })
    
    # Check developers
    try:
      config = get_config()
      developers = config.developers
      for dev_email in developers:
        dev_perms = result['existing_permissions'].get(dev_email)
        if not dev_perms or not dev_perms.get('has_can_manage'):
          result['missing_permissions'].append({
            'principal_type': 'user',
            'principal_id': dev_email,
            'principal_name': dev_email,
            'permission': 'CAN_MANAGE',
            'reason': 'Developer needs CAN_MANAGE'
          })
    except Exception:
      pass  # Config might not have developers
    
  except Exception as e:
    result['error'] = str(e)
  
  return result


def grant_permission(experiment_id: str, principal_type: str, principal_id: str, permission: str) -> bool:
  """Grant permission using the grant_experiment_permissions tool."""
  try:
    cmd = [
      'uv', 'run', 'python', 
      'tools/grant_experiment_permissions.py',
      '--experiment-id', experiment_id,
      '--principal-type', principal_type,
      '--principal-id', principal_id,
      '--permission', permission
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0
  except Exception:
    return False


def fix_permissions(
  experiment_id: str,
  analysis: Dict[str, Any],
  interactive: bool = True,
  dry_run: bool = False
) -> Dict[str, Any]:
  """Fix missing permissions."""
  result = {
    'fixed': [],
    'failed': [],
    'skipped': []
  }
  
  missing = analysis.get('missing_permissions', [])
  
  if not missing:
    result['message'] = 'No missing permissions to fix'
    return result
  
  # Show what will be done
  print(f'\n🔧 Found {len(missing)} missing permission(s):')
  for item in missing:
    print(f'  • {item["principal_name"]} ({item["principal_type"]}): {item["permission"]}')
    print(f'    Reason: {item["reason"]}')
  
  if dry_run:
    result['message'] = 'Dry run - no changes made'
    result['would_fix'] = missing
    return result
  
  if interactive:
    confirm = input('\nProceed with granting permissions? [y/N]: ')
    if confirm.lower() != 'y':
      result['message'] = 'Permission granting cancelled by user'
      result['skipped'] = missing
      return result
  
  # Grant permissions
  print('\nGranting permissions...')
  for item in missing:
    principal_name = item['principal_name']
    if grant_permission(
      experiment_id,
      item['principal_type'],
      item['principal_id'],
      item['permission']
    ):
      print(f'✅ Granted {item["permission"]} to {principal_name}')
      result['fixed'].append(principal_name)
    else:
      print(f'❌ Failed to grant permission to {principal_name}')
      result['failed'].append(principal_name)
  
  return result


def main():
  """Fix experiment permissions."""
  parser = argparse.ArgumentParser(
    description='Fix missing permissions for MLflow experiments'
  )
  parser.add_argument(
    'experiment_id',
    nargs='?',
    help='MLflow experiment ID (uses config if not provided)'
  )
  parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be done without making changes'
  )
  parser.add_argument(
    '--yes',
    action='store_true',
    help='Skip confirmation prompt'
  )
  parser.add_argument(
    '--format',
    choices=['json', 'text'],
    default='text',
    help='Output format (default: text)'
  )
  
  args = parser.parse_args()
  
  # Get experiment ID
  if not args.experiment_id:
    env_vars = load_env_local()
    args.experiment_id = env_vars.get('MLFLOW_EXPERIMENT_ID')
    
    if not args.experiment_id:
      print('❌ No experiment_id provided and MLFLOW_EXPERIMENT_ID not found in .env.local')
      sys.exit(1)
  
  # Analyze permissions
  analysis = analyze_permissions(args.experiment_id)
  
  if 'error' in analysis:
    if args.format == 'json':
      print(json.dumps({'error': analysis['error']}, indent=2))
    else:
      print(f'❌ Error: {analysis["error"]}')
    sys.exit(1)
  
  # Fix permissions
  fix_result = fix_permissions(
    args.experiment_id,
    analysis,
    interactive=not args.yes,
    dry_run=args.dry_run
  )
  
  # Combine results
  result = {
    'experiment_id': args.experiment_id,
    'analysis': analysis,
    'fix_result': fix_result
  }
  
  # Output results
  if args.format == 'json':
    print(json.dumps(result, indent=2, default=str))
  else:
    # Text output
    if fix_result.get('would_fix'):
      print(f'\n📋 Would fix {len(fix_result["would_fix"])} permission(s) (dry run)')
    elif fix_result.get('fixed'):
      print(f'\n✅ Fixed {len(fix_result["fixed"])} permission(s)')
    
    if fix_result.get('failed'):
      print(f'❌ Failed to fix {len(fix_result["failed"])} permission(s)')
      for principal in fix_result['failed']:
        print(f'  • {principal}')
    
    if fix_result.get('message'):
      print(f'\n{fix_result["message"]}')
  
  # Exit code
  if fix_result.get('failed'):
    sys.exit(1)
  else:
    sys.exit(0)


if __name__ == '__main__':
  main()