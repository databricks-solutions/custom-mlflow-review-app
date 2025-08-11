#!/usr/bin/env python3
"""Update the experiment_id in .env file."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict


def update_env_value(env_path: Path, key: str, value: str):
  """Update or add a value in .env file."""
  lines = []
  key_updated = False

  # Read existing lines
  if env_path.exists():
    with open(env_path, 'r') as f:
      lines = f.readlines()

  # Update existing key or mark for addition
  for i, line in enumerate(lines):
    if line.strip().startswith(f'{key}='):
      lines[i] = f'{key}={value}\n'
      key_updated = True
      break

  # Add new key if not found
  if not key_updated:
    lines.append(f'{key}={value}\n')

  # Write back to file
  with open(env_path, 'w') as f:
    f.writelines(lines)


def update_experiment_id(experiment_id: str) -> Dict[str, Any]:
  """Update the experiment_id in .env file.

  Args:
      experiment_id: The new experiment ID to set

  Returns:
      Updated configuration dictionary

  Raises:
      FileNotFoundError: If .env not found
      Exception: If unable to update config
  """
  env_path = Path('.env')

  if not env_path.exists():
    # Create .env if it doesn't exist
    with open(env_path, 'w') as f:
      f.write('# MLflow Review App Configuration\n')

  # Environment variables loaded by tools/__init__.py
  old_experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

  try:
    # Update .env file
    update_env_value(env_path, 'MLFLOW_EXPERIMENT_ID', experiment_id)

    return {
      'success': True,
      'old_experiment_id': old_experiment_id,
      'new_experiment_id': experiment_id,
      'env_path': str(env_path.absolute()),
      'message': 'Updated MLFLOW_EXPERIMENT_ID in .env',
    }

  except Exception as e:
    raise Exception(f'Failed to update .env: {str(e)}')


def main():
  """Update experiment_id in .env file."""
  parser = argparse.ArgumentParser(description='Update the experiment_id in .env')
  parser.add_argument('experiment_id', help='New experiment ID to set in .env')
  parser.add_argument(
    '--format', choices=['json', 'text'], default='text', help='Output format (default: text)'
  )

  args = parser.parse_args()

  try:
    result = update_experiment_id(args.experiment_id)

    if args.format == 'json':
      import json

      print(json.dumps(result, indent=2, default=str))
    else:
      print('✅ Updated .env successfully!')
      print(f'📄 File: {result["env_path"]}')
      if result['old_experiment_id']:
        print(f'🔄 Changed: {result["old_experiment_id"]} → {result["new_experiment_id"]}')
      else:
        print(f'🆕 Set experiment_id: {result["new_experiment_id"]}')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
