#!/usr/bin/env python3
"""Generate labeling schemas links for Databricks workspace."""

import argparse
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')


def get_labeling_schemas_link(experiment_id: str) -> str:
  """Generate a Databricks labeling schemas link.

  Args:
      experiment_id: The MLflow experiment ID

  Returns:
      Complete URL to the Databricks labeling schemas page

  Example:
      https://eng-ml-inference-team-us-west-2.cloud.databricks.com/ml/experiments/2178582188830602/label-schemas
  """
  # Get Databricks host from environment
  databricks_host = os.getenv('DATABRICKS_HOST')
  if not databricks_host:
    raise ValueError('DATABRICKS_HOST environment variable is not set')

  # Remove trailing slash if present
  databricks_host = databricks_host.rstrip('/')

  # Build the path
  path = f'/ml/experiments/{experiment_id}/label-schemas'

  # Construct full URL
  full_url = f'{databricks_host}{path}'

  return full_url


def main():
  """Generate Databricks labeling schemas link."""
  parser = argparse.ArgumentParser(
    description='Generate Databricks labeling schemas link',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    python get_labeling_schemas_link.py 2178582188830602

Environment Variables:
    DATABRICKS_HOST: Databricks workspace URL (required)
        """,
  )

  parser.add_argument('experiment_id', help='MLflow experiment ID')

  parser.add_argument(
    '--help-detailed', action='store_true', help='Show detailed help with examples'
  )

  if '--help-detailed' in os.sys.argv:
    print("""
Databricks Labeling Schemas Link Generator

This tool generates direct links to the Databricks labeling schemas management
interface for MLflow experiments.

URL Structure:
    https://{databricks_host}/ml/experiments/{experiment_id}/label-schemas

Parameters:
    experiment_id: The MLflow experiment ID

Environment Requirements:
    DATABRICKS_HOST: Your Databricks workspace URL
        Example: https://eng-ml-inference-team-us-west-2.cloud.databricks.com

Usage Examples:
    # Generate link for labeling schemas
    python get_labeling_schemas_link.py 2178582188830602

    # Open link directly in browser (macOS)
    open $(python get_labeling_schemas_link.py 2178582188830602)

    # Use with environment setup
    source .env.local && export DATABRICKS_HOST && python get_labeling_schemas_link.py 2178582188830602

Integration Notes:
    - Use this tool to quickly access the labeling schemas configuration
    - Link provides access to create, edit, and manage all labeling schemas for an experiment
    - Requires valid Databricks authentication when accessed
    - This is the centralized interface for schema management in Databricks
        """)
    return

  args = parser.parse_args()

  try:
    link = get_labeling_schemas_link(args.experiment_id)
    print(link)
  except Exception as e:
    print(f'Error: {e}')
    return 1

  return 0


if __name__ == '__main__':
  exit(main())
