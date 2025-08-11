#!/usr/bin/env python3
r"""Tool for logging expectations on MLflow traces.

This tool allows logging expectations on traces using the MLflow GenAI API.
Expectations are typically used for defining criteria or requirements upfront.

Usage:
    uv run python tools/log_expectation.py <trace_id> <expectation_key> \\
      <expectation_value> [--comment "Optional comment"]

Examples:
    # Log string expectation
    uv run python tools/log_expectation.py tr-123 response_format "JSON"

    # Log boolean expectation
    uv run python tools/log_expectation.py tr-123 should_include_sources true

    # Log numeric expectation with comment
    uv run python tools/log_expectation.py tr-123 max_response_time 5.0 \\
      --comment "Response should be under 5 seconds"

    # Log list expectation
    uv run python tools/log_expectation.py tr-123 required_fields "['name', 'email', 'phone']"

    # Log dictionary expectation
    uv run python tools/log_expectation.py tr-123 schema '{"type": "object", "required": ["id"]}'
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Union

from databricks.sdk import WorkspaceClient

# Add server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from utils.mlflow_utils import log_expectation


def parse_value(value_str: str) -> Union[str, int, float, bool, list, dict]:
  """Parse string value to appropriate Python type."""
  # Try to parse as JSON first (handles lists, dicts, booleans, numbers)
  try:
    return json.loads(value_str)
  except json.JSONDecodeError:
    # If JSON parsing fails, return as string
    return value_str


def log_trace_expectation(
  trace_id: str, expectation_key: str, expectation_value: Any, expectation_comment: str = None, username: str = 'unknown'
) -> dict:
  """Log expectation on a trace using direct MLflow utils."""
  return log_expectation(
    trace_id=trace_id,
    key=expectation_key,
    value=expectation_value,
    username=username,
    rationale=expectation_comment
  )


def main():
  """Main function to handle command line arguments and log expectations."""
  parser = argparse.ArgumentParser(
    description='Log expectations on MLflow traces',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=__doc__.split('Usage:')[1] if 'Usage:' in __doc__ else '',
  )

  parser.add_argument('trace_id', help='Trace ID to log expectation for')
  parser.add_argument(
    'expectation_key', help='Expectation key/name (e.g., "response_format", "required_fields")'
  )
  parser.add_argument(
    'expectation_value',
    help='Expectation value (string, number, boolean, JSON array, or JSON object)',
  )
  parser.add_argument('--rationale', help='Optional rationale for the expectation')
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

    # Parse the expectation value
    parsed_value = parse_value(args.expectation_value)

    print(f'🎯 Logging expectation on trace: {args.trace_id}')
    print(f'📋 Expectation Key: {args.expectation_key}')
    print(f'📝 Expectation Value: {parsed_value} (type: {type(parsed_value).__name__})')
    if args.rationale:
      print(f'💬 Rationale: {args.rationale}')

    if args.dry_run:
      print('\n🔍 DRY RUN - No expectation will be logged')
      return

    # Log the expectation
    result = log_trace_expectation(
      trace_id=args.trace_id,
      expectation_key=args.expectation_key,
      expectation_value=parsed_value,
      expectation_comment=args.rationale,
      username=username,
    )

    print('\n✅ Successfully logged expectation!')
    print(f'📋 Result: {result}')

  except Exception as e:
    print(f'\n❌ Error logging expectation: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
