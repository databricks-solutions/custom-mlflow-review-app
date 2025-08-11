#!/usr/bin/env python3
"""Generate labeling session links for Databricks workspace."""

import argparse
import json
import os
import subprocess
import sys
from urllib.parse import urlencode


def get_labeling_session_link(experiment_id: str, labeling_session_id: str) -> str:
  """Generate a Databricks labeling session link.

  Args:
      experiment_id: The MLflow experiment ID
      labeling_session_id: The labeling session ID

  Returns:
      Complete URL to the Databricks labeling session

  Example:
      https://eng-ml-inference-team-us-west-2.cloud.databricks.com/ml/experiments/2178582188830602/labeling-sessions?selectedLabelingSessionId=86c89a01-7f31-4cc0-b610-f88c6ab057c2
  """
  # Get Databricks host from environment
  databricks_host = os.getenv('DATABRICKS_HOST')
  if not databricks_host:
    raise ValueError('DATABRICKS_HOST environment variable is not set')

  # Remove trailing slash if present
  databricks_host = databricks_host.rstrip('/')

  # Build the base path
  base_path = f'/ml/experiments/{experiment_id}/labeling-sessions'

  # Add query parameter
  query_params = {'selectedLabelingSessionId': labeling_session_id}
  query_string = urlencode(query_params)

  # Construct full URL
  full_url = f'{databricks_host}{base_path}?{query_string}'

  return full_url


def find_labeling_session_by_name(session_name: str, experiment_id: str = None) -> str:
  """Find a labeling session ID by name.

  Args:
      session_name: The name/title of the labeling session to find
      experiment_id: Optional experiment ID to narrow search

  Returns:
      The labeling session ID if found

  Raises:
      ValueError: If session not found or multiple sessions with same name
  """
  try:
    # Call list_labeling_sessions.py to get all sessions
    cmd = [sys.executable, 'tools/list_labeling_sessions.py']
    if experiment_id:
      cmd.extend(['--experiment-id', experiment_id])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    sessions_data = json.loads(result.stdout)

    # Search for sessions matching the name
    matches = []
    sessions = sessions_data.get('labeling_sessions', [])

    for session in sessions:
      # Check if name matches (case-insensitive)
      if session.get('name', '').lower() == session_name.lower():
        matches.append(session)

    if not matches:
      raise ValueError(f"No labeling session found with name '{session_name}'")

    if len(matches) > 1:
      session_ids = [s.get('labeling_session_id', 'unknown') for s in matches]
      raise ValueError(
        f"Multiple labeling sessions found with name '{session_name}': {session_ids}"
      )

    session_id = matches[0].get('labeling_session_id')
    if not session_id:
      raise ValueError(f"Session '{session_name}' found but has no ID")

    return session_id

  except subprocess.CalledProcessError as e:
    raise ValueError(f'Failed to list labeling sessions: {e.stderr}')
  except json.JSONDecodeError:
    raise ValueError('Failed to parse labeling sessions response')


def main():
  """Generate Databricks labeling session link."""
  parser = argparse.ArgumentParser(
    description='Generate Databricks labeling session link',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    python get_labeling_session_link.py 2178582188830602 86c89a01-7f31-4cc0-b610-f88c6ab057c2

Environment Variables:
    DATABRICKS_HOST: Databricks workspace URL (required)
        """,
  )

  parser.add_argument('experiment_id', help='MLflow experiment ID')

  parser.add_argument(
    'labeling_session_id',
    help='Labeling session ID or name (will search by name if not a valid UUID)',
  )

  parser.add_argument(
    '--by-name', action='store_true', help='Force search by name instead of treating as ID'
  )

  parser.add_argument(
    '--help-detailed', action='store_true', help='Show detailed help with examples'
  )

  if '--help-detailed' in os.sys.argv:
    print("""
Databricks Labeling Session Link Generator

This tool generates direct links to Databricks labeling sessions for easy access
to the MLflow evaluation interface.

URL Structure:
    https://{databricks_host}/ml/experiments/{experiment_id}/labeling-sessions?selectedLabelingSessionId={labeling_session_id}

Parameters:
    experiment_id: The MLflow experiment ID containing the traces
    labeling_session_id: The specific labeling session ID to open

Environment Requirements:
    DATABRICKS_HOST: Your Databricks workspace URL
        Example: https://eng-ml-inference-team-us-west-2.cloud.databricks.com

Usage Examples:
    # Generate link for a specific labeling session
    python get_labeling_session_link.py 2178582188830602 86c89a01-7f31-4cc0-b610-f88c6ab057c2

    # Open link directly in browser (macOS)
    open $(python get_labeling_session_link.py 2178582188830602 86c89a01-7f31-4cc0-b610-f88c6ab057c2)

    # Use with environment setup
    source .env.local && export DATABRICKS_HOST && python get_labeling_session_link.py 2178582188830602 86c89a01-7f31-4cc0-b610-f88c6ab057c2

Integration Notes:
    - Use this tool to generate links for sharing with reviewers
    - Links provide direct access to the labeling interface
    - Requires valid Databricks authentication when accessed
    - Links work for both internal team members and external reviewers (with proper permissions)
        """)
    return

  args = parser.parse_args()

  try:
    session_id = args.labeling_session_id

    # Determine if we should search by name
    should_search_by_name = args.by_name or (
      # If it's not a UUID-like string, assume it's a name
      not (len(session_id) == 36 and session_id.count('-') == 4)
    )

    if should_search_by_name:
      # Search for session by name
      print(f"Searching for labeling session named '{session_id}'...", file=sys.stderr)
      session_id = find_labeling_session_by_name(session_id, args.experiment_id)
      print(f'Found session ID: {session_id}', file=sys.stderr)

    link = get_labeling_session_link(args.experiment_id, session_id)
    print(link)
  except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    return 1

  return 0


if __name__ == '__main__':
  exit(main())
