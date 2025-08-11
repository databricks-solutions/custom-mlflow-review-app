#!/usr/bin/env python3
"""Get review app by ID or experiment ID."""

import argparse
import asyncio
import inspect
import json
import sys

from server.utils.config import config
from server.utils.review_apps_utils import review_apps_utils


async def main():
  """Get review app."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(review_apps_utils.get_review_app)
  description = func_doc.split('\n')[0] if func_doc else 'Get review app by ID or experiment ID'

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('--review-app-id', help='Review app ID')
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')

  args = parser.parse_args()

  try:
    # Validate arguments
    if args.review_app_id and args.experiment_id:
      print('❌ Error: Cannot specify both --review-app-id and --experiment-id', file=sys.stderr)
      sys.exit(1)

    if args.review_app_id:
      result = await review_apps_utils.get_review_app(review_app_id=args.review_app_id)
    else:
      # Use provided experiment_id or default to config
      experiment_id = args.experiment_id or config.experiment_id
      result = await review_apps_utils.get_review_app_by_experiment(experiment_id=experiment_id)

    print(json.dumps(result, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
