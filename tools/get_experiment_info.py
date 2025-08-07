#!/usr/bin/env python3
"""Get detailed information about an MLflow experiment by name or ID."""

import argparse
import json
import sys
from typing import Any, Dict

import mlflow

from server.utils.mlflow_utils import get_experiment, search_traces
from server.utils.user_utils import user_utils


def _build_experiment_info(experiment_data: Dict[str, Any]) -> Dict[str, Any]:
  """Build experiment info dictionary with trace count and URLs."""
  experiment_id = experiment_data['experiment_id']

  # Get trace count for this experiment
  raw_traces = search_traces(experiment_ids=[experiment_id], max_results=1)

  # Get workspace URL from user utils
  workspace_url = user_utils.get_workspace_url()
  experiment_url = f'{workspace_url}/ml/experiments/{experiment_id}/traces'

  return {
    'experiment_id': experiment_id,
    'name': experiment_data['name'],
    'artifact_location': experiment_data.get('artifact_location', ''),
    'lifecycle_stage': experiment_data.get('lifecycle_stage', 'active'),
    'creation_time': experiment_data.get('creation_time'),
    'last_update_time': experiment_data.get('last_update_time'),
    'experiment_url': experiment_url,
    'workspace_url': workspace_url,
    'trace_count': len(raw_traces) if raw_traces else 0,
    'has_traces': bool(raw_traces),
  }


def get_experiment_info(experiment_identifier: str) -> Dict[str, Any]:
  """Get experiment information by name or ID.

  Args:
      experiment_identifier: Either experiment ID or experiment name

  Returns:
      Dictionary with experiment information

  Raises:
      ValueError: If experiment not found
  """
  try:
    # First try to get by ID (if it looks like an ID)
    if experiment_identifier.isdigit():
      experiment_result = get_experiment(experiment_identifier)
      if experiment_result and 'experiment' in experiment_result:
        return _build_experiment_info(experiment_result['experiment'])

    # Try to search by name using MLflow client directly
    client = mlflow.tracking.MlflowClient()
    experiments = client.search_experiments()
    for exp in experiments:
      if exp.name == experiment_identifier or exp.experiment_id == experiment_identifier:
        return _build_experiment_info(
          {
            'experiment_id': exp.experiment_id,
            'name': exp.name,
            'artifact_location': exp.artifact_location,
            'lifecycle_stage': exp.lifecycle_stage,
            'creation_time': exp.creation_time,
            'last_update_time': exp.last_update_time,
          }
        )

    # If not found, raise error
    raise ValueError(f"Experiment '{experiment_identifier}' not found")

  except Exception as e:
    raise ValueError(f'Failed to get experiment info: {str(e)}')


def main():
  """Get experiment information by name or ID."""
  parser = argparse.ArgumentParser(
    description='Get detailed information about an MLflow experiment by name or ID'
  )
  parser.add_argument('experiment', help='Experiment ID or experiment name')
  parser.add_argument(
    '--format', choices=['json', 'text'], default='json', help='Output format (default: json)'
  )

  args = parser.parse_args()

  try:
    experiment_info = get_experiment_info(args.experiment)

    if args.format == 'json':
      print(json.dumps(experiment_info, indent=2, default=str))
    else:
      # Pretty text format with proper line breaks
      print(f'📊 Experiment: {experiment_info["name"]}')
      print(f'🆔 ID: {experiment_info["experiment_id"]}')
      print(f'🔗 URL: {experiment_info["experiment_url"]}')
      print(f'📈 Traces: {experiment_info["trace_count"]}')
      print(f'📁 Artifact Location: {experiment_info["artifact_location"]}')
      print(f'🔄 Status: {experiment_info["lifecycle_stage"]}')
      print()  # Add blank line at end

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
