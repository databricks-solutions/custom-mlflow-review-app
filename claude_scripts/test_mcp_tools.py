#!/usr/bin/env python3
"""Test script to directly call MCP server tools."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Load environment variables from .env.local if it exists
def load_env_file(filepath: str) -> None:
  """Load environment variables from a file."""
  env_path = project_root / filepath
  if env_path.exists():
    with open(env_path) as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
          key, _, value = line.partition('=')
          if key and value:
            os.environ[key] = value


# Load .env files
load_env_file('.env')
load_env_file('.env.local')

# Import the utility functions directly (after path setup)
from server.utils.user_utils import user_utils


def main():
  """Test the MCP tools directly."""
  print('Testing MCP tools directly...')

  # Test get current user
  print('\n1. Getting current user:')
  result = user_utils.get_current_user()
  print(f'Result: {result}')

  # Test get workspace info
  print('\n2. Getting workspace info:')
  result = user_utils.get_user_workspace_info()
  print(f'Result: {result}')

  # Example: Search traces (you'll need actual experiment IDs)
  # print("\n3. Searching traces:")
  # result = mlflow_utils.search_traces(experiment_ids=["your_experiment_id"])
  # print(f"Result: {result}")


if __name__ == '__main__':
  main()
