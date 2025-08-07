#!/usr/bin/env python3
r"""Tool for logging feedback on MLflow traces.

This tool allows logging feedback on traces using the MLflow GenAI API.
Feedback is typically used for evaluating traces after they've been generated.

Usage:
    uv run python tools/log_feedback.py <trace_id> <feedback_key> \\
      <feedback_value> [--comment "Optional comment"]

Examples:
    # Log numeric feedback
    uv run python tools/log_feedback.py tr-123 quality 4

    # Log boolean feedback
    uv run python tools/log_feedback.py tr-123 is_helpful true

    # Log string feedback with comment
    uv run python tools/log_feedback.py tr-123 category "excellent" \\
      --comment "Very thorough response"

    # Log list feedback
    uv run python tools/log_feedback.py tr-123 issues "['accuracy', 'completeness']"
"""

import argparse
import json
import sys
from typing import Any, Union

import requests
from databricks.sdk import WorkspaceClient

from server.utils.databricks_auth import get_databricks_headers


def parse_value(value_str: str) -> Union[str, int, float, bool, list]:
  """Parse string value to appropriate Python type."""
  # Try to parse as JSON first (handles lists, booleans, numbers)
  try:
    return json.loads(value_str)
  except json.JSONDecodeError:
    # If JSON parsing fails, return as string
    return value_str


def log_trace_feedback(
  trace_id: str, feedback_key: str, feedback_value: Any, feedback_comment: str = None
) -> dict:
  """Log feedback on a trace via the API endpoint."""
  base_url = 'http://localhost:8000'

  url = f'{base_url}/api/mlflow/traces/{trace_id}/feedback'

  headers = get_databricks_headers()
  headers['Content-Type'] = 'application/json'

  payload = {
    'feedback_key': feedback_key,
    'feedback_value': feedback_value,
  }

  if feedback_comment:
    payload['feedback_comment'] = feedback_comment

  response = requests.post(url, json=payload, headers=headers)

  if response.status_code == 200:
    return response.json()
  else:
    try:
      error_detail = response.json()
      raise Exception(f'API Error: {error_detail}')
    except (ValueError, KeyError):
      raise Exception(f'HTTP {response.status_code}: {response.text}')


def main():
  """Main function to handle command line arguments and log feedback."""
  parser = argparse.ArgumentParser(
    description='Log feedback on MLflow traces',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=__doc__.split('Usage:')[1] if 'Usage:' in __doc__ else '',
  )

  parser.add_argument('trace_id', help='Trace ID to log feedback for')
  parser.add_argument('feedback_key', help='Feedback key/name (e.g., "quality", "helpfulness")')
  parser.add_argument(
    'feedback_value', help='Feedback value (string, number, boolean, or JSON array)'
  )
  parser.add_argument('--comment', help='Optional comment/rationale for the feedback')
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be logged without actually logging'
  )

  args = parser.parse_args()

  try:
    # Get the current user from Databricks
    try:
      client = WorkspaceClient()
      current_user = client.current_user.me()
      username = current_user.user_name or 'unknown'
      print(f'👤 User: {username}')
    except Exception as e:
      print(f'⚠️ Could not get current user: {str(e)}')
      username = 'unknown'

    # Parse the feedback value
    parsed_value = parse_value(args.feedback_value)

    print(f'🎯 Logging feedback on trace: {args.trace_id}')
    print(f'📊 Feedback Key: {args.feedback_key}')
    print(f'📈 Feedback Value: {parsed_value} (type: {type(parsed_value).__name__})')
    if args.comment:
      print(f'💬 Comment: {args.comment}')

    if args.dry_run:
      print('\n🔍 DRY RUN - No feedback will be logged')
      return

    # Log the feedback
    result = log_trace_feedback(
      trace_id=args.trace_id,
      feedback_key=args.feedback_key,
      feedback_value=parsed_value,
      feedback_comment=args.comment,
    )

    print('\n✅ Successfully logged feedback!')
    print(f'📋 Result: {result}')

  except Exception as e:
    print(f'\n❌ Error logging feedback: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
