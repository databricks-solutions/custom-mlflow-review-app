#!/usr/bin/env python3
"""Get URLs for traces in labeling sessions."""

import argparse
import asyncio
import json
import sys
from typing import Dict, List

from server.utils.labeling_sessions_utils import get_labeling_session, list_labeling_sessions
from server.utils.mlflow_utils import search_traces


async def get_trace_urls_for_session(
  review_app_id: str, labeling_session_id: str, databricks_host: str
) -> List[Dict[str, str]]:
  """Get trace URLs for a specific labeling session."""
  try:
    # Get the labeling session details
    session = await get_labeling_session(
      review_app_id=review_app_id, labeling_session_id=labeling_session_id
    )

    # Get the MLflow run ID
    mlflow_run_id = session.get('mlflow_run_id')
    if not mlflow_run_id:
      return []

    # Search for traces linked to this run
    # Get experiment_id from environment or config
    import os

    import yaml
    # Environment variables loaded by tools/__init__.py

    experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

    if not experiment_id:
      # Fallback to config.yaml
      try:
        with open('config.yaml', 'r') as f:
          config = yaml.safe_load(f)
        experiment_id = config['mlflow']['experiment_id']
      except Exception as e:
        raise ValueError(f'No experiment_id found in environment or config.yaml: {e}')

    raw_traces = search_traces(
      experiment_ids=[experiment_id], filter_string=f"run = '{mlflow_run_id}'"
    )

    # Convert raw traces to expected format
    traces = []
    for trace in raw_traces:
      traces.append(
        {
          'info': {
            'request_id': trace.info.trace_id,
            'experiment_id': trace.info.experiment_id,
          }
        }
      )

    # Construct URLs for each trace
    trace_urls = []
    for trace in traces:
      trace_id = trace.get('info', {}).get('request_id')
      experiment_id = trace.get('info', {}).get('experiment_id')

      if trace_id and experiment_id:
        trace_url = f'{databricks_host}/ml/experiments/{experiment_id}/traces/{trace_id}'
        trace_urls.append({'trace_id': trace_id, 'experiment_id': experiment_id, 'url': trace_url})

    return trace_urls

  except Exception as e:
    print(f'❌ Error getting traces for session {labeling_session_id}: {str(e)}', file=sys.stderr)
    return []


async def main():
  """Get trace URLs for labeling sessions."""
  parser = argparse.ArgumentParser(description='Get URLs for traces in labeling sessions')
  parser.add_argument('review_app_id', help='Review app ID')
  parser.add_argument('--session-id', help='Specific labeling session ID (optional)')
  parser.add_argument(
    '--host', help='Databricks host URL (optional, reads from env if not provided)'
  )

  args = parser.parse_args()

  # Get Databricks host
  databricks_host = args.host
  if not databricks_host:
    import os

    databricks_host = os.getenv('DATABRICKS_HOST')
    if not databricks_host:
      print(
        '❌ Error: DATABRICKS_HOST not found in environment or provided as argument',
        file=sys.stderr,
      )
      sys.exit(1)

  # Remove trailing slash if present
  databricks_host = databricks_host.rstrip('/')

  try:
    if args.session_id:
      # Get URLs for specific session
      session = await get_labeling_session(
        review_app_id=args.review_app_id, labeling_session_id=args.session_id
      )

      trace_urls = await get_trace_urls_for_session(
        args.review_app_id, args.session_id, databricks_host
      )

      result = {
        'session': {
          'id': args.session_id,
          'name': session.get('name', 'Unknown'),
          'mlflow_run_id': session.get('mlflow_run_id'),
        },
        'traces': trace_urls,
      }

    else:
      # Get URLs for all sessions
      sessions_response = await list_labeling_sessions(review_app_id=args.review_app_id)

      sessions = sessions_response.get('labeling_sessions', [])
      result = {'sessions': []}

      for session in sessions:
        session_id = session.get('labeling_session_id')
        trace_urls = await get_trace_urls_for_session(
          args.review_app_id, session_id, databricks_host
        )

        result['sessions'].append(
          {
            'session': {
              'id': session_id,
              'name': session.get('name', 'Unknown'),
              'mlflow_run_id': session.get('mlflow_run_id'),
            },
            'traces': trace_urls,
          }
        )

    print(json.dumps(result, indent=2))

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
