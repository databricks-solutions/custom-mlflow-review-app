#!/usr/bin/env python3
"""Link traces to a labeling session."""

import argparse
import inspect
import json
import sys

from dotenv import load_dotenv

from server.utils.labeling_sessions_utils import link_traces_to_session

# Load environment variables
load_dotenv()
load_dotenv('.env.local')


def main():
  """Link traces to session."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(link_traces_to_session)
  description = (
    func_doc.split('\n')[0]
    if func_doc
    else 'Link traces to a labeling session and create labeling items'
  )

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('review_app_id', help='Review app ID')
  parser.add_argument('labeling_session_id', help='Labeling session ID')
  parser.add_argument('mlflow_run_id', help='MLflow run ID')
  parser.add_argument('trace_ids', nargs='+', help='Trace IDs to link')

  args = parser.parse_args()

  try:
    import asyncio

    result = asyncio.run(
      link_traces_to_session(
        review_app_id=args.review_app_id,
        labeling_session_id=args.labeling_session_id,
        mlflow_run_id=args.mlflow_run_id,
        trace_ids=args.trace_ids,
      )
    )
    print(json.dumps(result, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
