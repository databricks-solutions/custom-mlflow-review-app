#!/usr/bin/env python3
"""Update expectation on a trace using MLflow SDK."""

import argparse
import sys
from pathlib import Path

# Add server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from utils.mlflow_utils import update_expectation


def main():
  parser = argparse.ArgumentParser(
    description='Update existing expectation on a trace',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Update expectation value (boolean)
  python tools/update_expectation.py tr-abc123 a-def456 true

  # Update expectation with rationale
  python tools/update_expectation.py tr-abc123 a-def456 false --rationale "New reasoning"

  # Update expectation with username
  python tools/update_expectation.py tr-abc123 a-def456 true --username "user@example.com"
        """,
  )

  parser.add_argument('trace_id', help='The trace ID to update expectation on')
  parser.add_argument('assessment_id', help='The assessment ID to update')
  parser.add_argument('value', help='The new expectation value (true/false/string/number)')
  parser.add_argument('--rationale', help='Optional rationale for the expectation update')
  parser.add_argument(
    '--username', default='cli_user', help='Username providing the expectation (default: cli_user)'
  )

  args = parser.parse_args()

  # Convert string values to appropriate types
  value = args.value
  if value.lower() == 'true':
    value = True
  elif value.lower() == 'false':
    value = False
  elif value.isdigit():
    value = int(value)
  else:
    try:
      value = float(value)
    except ValueError:
      # Keep as string
      pass

  try:
    print(f'Updating expectation on trace {args.trace_id[:8]}...')
    print(f'Assessment ID: {args.assessment_id}')
    print(f'New value: {value}')
    if args.rationale:
      print(f'Rationale: {args.rationale}')
    print(f'Username: {args.username}')

    result = update_expectation(
      trace_id=args.trace_id,
      assessment_id=args.assessment_id,
      value=value,
      username=args.username,
      rationale=args.rationale,
    )

    print(f"\n✅ {result['message']}")
    print(f"Assessment ID: {result['assessment_id']}")

  except Exception as e:
    print(f'❌ Error updating expectation: {e}')
    sys.exit(1)


if __name__ == '__main__':
  main()
