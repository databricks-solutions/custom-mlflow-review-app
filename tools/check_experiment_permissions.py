#!/usr/bin/env python3
"""Check permissions for an MLflow experiment.

This tool checks permissions for any experiment type (regular or notebook-style),
showing who has access and what level of permissions they have.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from server.utils.permissions import (
    AccessControlEntry,
    get_experiment_permissions,
    get_experiment_permissions_unified,
    is_notebook_experiment,
)
from server.utils.mlflow_utils import get_experiment


def check_permissions(experiment_id: str, app_name: Optional[str] = None) -> Dict[str, Any]:
  """Check permissions for an experiment.
  
  Args:
      experiment_id: The MLflow experiment ID
      app_name: Optional app name to check service principal permissions
      
  Returns:
      Dictionary with permission details
  """
  result = {
    'experiment_id': experiment_id,
    'status': 'OK',
    'is_notebook_experiment': False,
    'permissions': {},
    'summary': {},
    'issues': [],
  }
  
  try:
    # Check if it's a notebook experiment
    result['is_notebook_experiment'] = is_notebook_experiment(experiment_id)
    
    # Get experiment info
    try:
      exp_info = get_experiment(experiment_id)
      if exp_info and 'experiment' in exp_info:
        result['experiment_name'] = exp_info['experiment'].get('name', 'Unknown')
    except Exception:
      result['experiment_name'] = 'Unknown'
    
    # Get permissions
    acl_list = get_experiment_permissions(experiment_id)
    
    # Process permissions
    current_permissions = {}
    for acl in acl_list:
      # Determine principal
      principal = acl.user_name or acl.group_name or acl.service_principal_name
      if not principal:
        continue
        
      # Determine type
      if acl.user_name:
        principal_type = 'user'
      elif acl.group_name:
        principal_type = 'group'
      else:
        principal_type = 'service_principal'
      
      # Extract permission levels
      permission_levels = []
      for perm in acl.all_permissions:
        if not perm.inherited:  # Only show direct permissions
          permission_levels.append(perm.permission_level)
      
      if permission_levels:  # Only add if there are direct permissions
        current_permissions[principal] = {
          'type': principal_type,
          'permissions': permission_levels,
          'has_can_manage': 'CAN_MANAGE' in permission_levels,
          'has_can_edit': 'CAN_EDIT' in permission_levels or 'CAN_MANAGE' in permission_levels,
        }
    
    result['permissions'] = current_permissions
    
    # Generate summary statistics
    total_users = sum(1 for p in current_permissions.values() if p['type'] == 'user')
    total_sps = sum(1 for p in current_permissions.values() if p['type'] == 'service_principal')
    total_groups = sum(1 for p in current_permissions.values() if p['type'] == 'group')
    
    can_manage_users = sum(
      1 for p in current_permissions.values() 
      if p['type'] == 'user' and p['has_can_manage']
    )
    can_manage_sps = sum(
      1 for p in current_permissions.values() 
      if p['type'] == 'service_principal' and p['has_can_manage']
    )
    
    result['summary'] = {
      'total_principals': len(current_permissions),
      'total_users': total_users,
      'total_service_principals': total_sps,
      'total_groups': total_groups,
      'users_with_can_manage': can_manage_users,
      'service_principals_with_can_manage': can_manage_sps,
    }
    
    # Check for missing permissions on required principals
    # Check app service principal if app_name provided
    if app_name:
      try:
        import subprocess
        # Get app service principal from app_status
        sp_result = subprocess.run(
          ['uv', 'run', 'python', 'app_status.py', '--format', 'json'],
          capture_output=True,
          text=True,
          timeout=30
        )
        if sp_result.returncode == 0:
          import json
          status_data = json.loads(sp_result.stdout)
          app_status = status_data.get('app_status', {})
          
          # For notebook experiments, we need the service_principal_client_id (UUID)
          sp_id = app_status.get('service_principal_client_id')
          sp_name = app_status.get('service_principal_name')
          
          if sp_id:
            # Check if service principal has CAN_MANAGE (use UUID for lookup)
            sp_perms = current_permissions.get(sp_id, {})
            if not sp_perms.get('has_can_manage'):
              result['issues'].append(f'App service principal {sp_name or sp_id} is missing CAN_MANAGE permission')
              result['status'] = 'MISSING_PERMISSIONS'
            
            # Add to summary
            result['summary']['app_service_principal'] = {
              'name': sp_name or sp_id,
              'id': sp_id,
              'has_can_manage': sp_perms.get('has_can_manage', False),
              'permissions': sp_perms.get('permissions', []),
            }
      except Exception:
        pass  # Ignore errors getting app status
    
    # Check current user
    try:
      from databricks.sdk import WorkspaceClient
      w = WorkspaceClient()
      current_user = w.current_user.me()
      if current_user and current_user.user_name:
        user_perms = current_permissions.get(current_user.user_name, {})
        if not user_perms.get('has_can_manage'):
          result['issues'].append(f'Current user {current_user.user_name} is missing CAN_MANAGE permission')
          result['status'] = 'MISSING_PERMISSIONS'
    except Exception:
      pass  # Ignore errors getting current user
    
    # Check developers from config
    try:
      from server.utils.config import get_config
      config = get_config()
      developers = config.developers
      for dev_email in developers:
        dev_perms = current_permissions.get(dev_email, {})
        if not dev_perms.get('has_can_manage'):
          result['issues'].append(f'Developer {dev_email} is missing CAN_MANAGE permission')
          result['status'] = 'MISSING_PERMISSIONS'
          
      # Add developers to summary
      developers_summary = []
      for dev_email in developers:
        dev_perms = current_permissions.get(dev_email, {})
        developers_summary.append({
          'email': dev_email,
          'has_can_manage': dev_perms.get('has_can_manage', False),
          'permissions': dev_perms.get('permissions', []),
        })
      result['summary']['developers'] = developers_summary
    except Exception:
      pass  # Config might not have developers
    
  except Exception as e:
    result['status'] = 'ERROR'
    result['error'] = str(e)
  
  return result


def format_text_output(check_result: Dict[str, Any]) -> str:
  """Format the check result as human-readable text."""
  lines = []
  
  lines.append('🔍 MLflow Experiment Permissions Check')
  lines.append('=' * 40)
  lines.append(f'Experiment ID: {check_result["experiment_id"]}')
  if 'experiment_name' in check_result:
    lines.append(f'Experiment Name: {check_result["experiment_name"]}')
  lines.append(f'Type: {"Notebook" if check_result["is_notebook_experiment"] else "Regular"} Experiment')
  lines.append('')
  
  if check_result.get('error'):
    lines.append(f'❌ Error: {check_result["error"]}')
    return '\n'.join(lines)
  
  # Display permissions
  lines.append('🔐 CURRENT PERMISSIONS')
  lines.append('-' * 20)
  
  permissions = check_result.get('permissions', {})
  if not permissions:
    lines.append('  No permissions found')
  else:
    # Group by type
    users = [(k, v) for k, v in permissions.items() if v['type'] == 'user']
    service_principals = [(k, v) for k, v in permissions.items() if v['type'] == 'service_principal']
    groups = [(k, v) for k, v in permissions.items() if v['type'] == 'group']
    
    if users:
      lines.append('  Users:')
      for principal, info in sorted(users):
        perms = ', '.join(info['permissions'])
        lines.append(f'    • {principal}: {perms}')
    
    if service_principals:
      lines.append('  Service Principals:')
      for principal, info in sorted(service_principals):
        perms = ', '.join(info['permissions'])
        lines.append(f'    • {principal}: {perms}')
    
    if groups:
      lines.append('  Groups:')
      for principal, info in sorted(groups):
        perms = ', '.join(info['permissions'])
        lines.append(f'    • {principal}: {perms}')
  
  lines.append('')
  
  # Statistics
  summary = check_result.get('summary', {})
  if summary:
    lines.append('📊 STATISTICS')
    lines.append('-' * 13)
    lines.append(f'Total principals: {summary.get("total_principals", 0)}')
    lines.append(f'  Users: {summary.get("total_users", 0)} ({summary.get("users_with_can_manage", 0)} with CAN_MANAGE)')
    lines.append(f'  Service Principals: {summary.get("total_service_principals", 0)} ({summary.get("service_principals_with_can_manage", 0)} with CAN_MANAGE)')
    lines.append(f'  Groups: {summary.get("total_groups", 0)}')
  
  return '\n'.join(lines)


def main():
  """Check experiment permissions."""
  parser = argparse.ArgumentParser(
    description='Check permissions for an MLflow experiment (handles both regular and notebook experiments)'
  )
  parser.add_argument(
    'experiment_id',
    help='MLflow experiment ID'
  )
  parser.add_argument(
    '--app-name',
    help='App name to check service principal permissions'
  )
  parser.add_argument(
    '--format',
    choices=['json', 'text'],
    default='text',
    help='Output format (default: text)'
  )
  
  args = parser.parse_args()
  
  # Check permissions
  result = check_permissions(args.experiment_id, args.app_name)
  
  # Output results
  if args.format == 'json':
    print(json.dumps(result, indent=2, default=str))
  else:
    print(format_text_output(result))
  
  # Exit code based on status
  sys.exit(0 if result['status'] == 'OK' else 1)


if __name__ == '__main__':
  main()