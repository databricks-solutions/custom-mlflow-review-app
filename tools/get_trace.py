#!/usr/bin/env python3
"""Get a specific trace by ID."""

import argparse
import inspect
import json
import sys

from server.utils.mlflow_utils import get_trace


def main():
  """Get a specific trace."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(get_trace)
  description = func_doc.split('\n')[0] if func_doc else 'Get a specific trace by ID'

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('trace_id', help='Trace ID to retrieve')

  args = parser.parse_args()

  try:
    # Get raw trace and use built-in to_json method
    raw_trace = get_trace(trace_id=args.trace_id)
    trace_json = raw_trace.to_json()
    # Parse and pretty-print the JSON
    trace_dict = json.loads(trace_json)
    print(json.dumps(trace_dict, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
