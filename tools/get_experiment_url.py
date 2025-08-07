#!/usr/bin/env python3
"""Get the experiment URL for the configured experiment."""

import argparse
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.local')


def main():
  """Get experiment URL."""
  parser = argparse.ArgumentParser(description='Get the MLflow experiment URL')
  parser.add_argument(
    '--experiment-id', help='Specific experiment ID (optional, uses config if not provided)'
  )
  parser.add_argument(
    '--host', help='Databricks host URL (optional, reads from env if not provided)'
  )

  args = parser.parse_args()

  # Get experiment ID
  experiment_id = args.experiment_id
  if not experiment_id:
    # Try environment variable first
    experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

    # Exit if no experiment_id found in environment
    if not experiment_id:
      print('❌ Error: No experiment_id found in environment variables', file=sys.stderr)
      print(
        '   Set MLFLOW_EXPERIMENT_ID environment variable or use --experiment-id', file=sys.stderr
      )
      sys.exit(1)

  # Get Databricks host
  databricks_host = args.host
  if not databricks_host:
    databricks_host = os.getenv('DATABRICKS_HOST')
    if not databricks_host:
      print(
        '❌ Error: DATABRICKS_HOST not found in environment or provided as argument',
        file=sys.stderr,
      )
      sys.exit(1)

  # Remove trailing slash if present
  databricks_host = databricks_host.rstrip('/')

  # Construct and print URL
  experiment_url = f'{databricks_host}/ml/experiments/{experiment_id}/traces'
  print(experiment_url)


if __name__ == '__main__':
  main()
