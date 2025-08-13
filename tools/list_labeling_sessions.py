#!/usr/bin/env python3
"""List labeling sessions for a review app."""

import argparse
import asyncio
import inspect
import json
import sys

from server.utils.config import config
from server.utils.labeling_sessions_utils import list_labeling_sessions
from server.utils.review_apps_utils import review_apps_utils

# Import analysis functions from analyze_labeling_results
sys.path.append('.')
from tools.analyze_labeling_results import analyze_session


async def main():
  """List labeling sessions with their associated schemas and analysis."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(list_labeling_sessions)
  description = func_doc.split('\n')[0] if func_doc else 'List labeling sessions for a review app'

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('--review-app-id', help='Review app ID (defaults to current experiment)')
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('--filter', dest='filter_string', help='Filter string')

  args = parser.parse_args()

  try:
    # Validate arguments
    if args.review_app_id and args.experiment_id:
      print('❌ Error: Cannot specify both --review-app-id and --experiment-id', file=sys.stderr)
      sys.exit(1)

    # Get review app ID
    if args.review_app_id:
      review_app_id = args.review_app_id
      review_app = await review_apps_utils.get_review_app(review_app_id=review_app_id)
    else:
      # Use provided experiment_id or default to config
      experiment_id = args.experiment_id or config.experiment_id
      review_app = await review_apps_utils.get_review_app_by_experiment(experiment_id=experiment_id)
      review_app_id = review_app.get('review_app_id')

    # Get labeling sessions
    sessions_result = await list_labeling_sessions(
      review_app_id=review_app_id, filter_string=args.filter_string
    )

    # Always get review app details to fetch full schema information
    review_app_schemas = review_app.get('labeling_schemas', [])

    # Enhance sessions with full schema details and analysis
    sessions = sessions_result.get('labeling_sessions', [])
    for session in sessions:
      session_schema_refs = session.get('labeling_schemas', [])
      session_schema_names = {ref.get('name') for ref in session_schema_refs}

      # Find full schema details from review app schemas
      session['full_schemas'] = [
        schema for schema in review_app_schemas if schema.get('name') in session_schema_names
      ]

      # Always add analysis
      session_id = session.get('labeling_session_id')
      session_name = session.get('name', f'Session {session_id}')

      try:
        analysis = await analyze_session(
          review_app_id=review_app_id,
          session_id=session_id,
          session_name=session_name,
          schemas=session['full_schemas'],
        )
        session['analysis'] = analysis
      except Exception as e:
        session['analysis'] = {'error': f'Analysis failed: {str(e)}', 'session_name': session_name}

    print(json.dumps(sessions_result, indent=2, default=str))

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
