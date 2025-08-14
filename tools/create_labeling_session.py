#!/usr/bin/env python3
"""Create a labeling session for a review app."""

import argparse
import asyncio
import json
import sys

from server.utils.labeling_sessions_utils import create_labeling_session
from tools.utils.review_app_resolver import resolve_review_app_id


async def main():
  """Create a labeling session for a review app."""
  parser = argparse.ArgumentParser(
    description='Create a labeling session for a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Create a basic labeling session (uses current experiment)
  python create_labeling_session.py --name "Quality Review Session" --users user1@example.com user2@example.com

  # Create with specific review app ID
  python create_labeling_session.py review_app_id --name "Helpfulness Review" --users reviewer@example.com --schemas quality_rating helpfulness

  # Create with specific experiment ID
  python create_labeling_session.py --experiment-id exp123 --name "June Evaluation" --users team@example.com --description "Monthly quality evaluation for June traces"

  # Create from JSON template
  python create_labeling_session.py --from-file session_config.json

JSON file format:
{
  "name": "Session Name",
  "description": "Session description",
  "assigned_users": ["user1@example.com"],
  "labeling_schemas": [{"name": "quality_rating"}, {"name": "helpfulness"}]
}
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')

  # Session creation options
  creation_group = parser.add_mutually_exclusive_group(required=True)
  creation_group.add_argument('--name', help='Name of the labeling session')
  creation_group.add_argument('--from-file', help='Create session from JSON file')

  # Session details
  parser.add_argument('--users', nargs='+', help='Assigned users (email addresses)')
  parser.add_argument('--description', help='Session description')
  parser.add_argument(
    '--schemas',
    nargs='+',
    help='Specific labeling schema names to use (default: all schemas from review app)',
  )

  # Options
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be created without actually creating'
  )

  args = parser.parse_args()

  try:
    # Resolve review app ID and get the review app
    review_app_id, review_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )
    available_schemas = review_app.get('labeling_schemas', [])
    available_schema_names = {schema['name'] for schema in available_schemas}

    if not available_schemas:
      print('❌ Review app has no labeling schemas. Create schemas first.', file=sys.stderr)
      sys.exit(1)

    # Build session data
    session_data = {}

    if args.from_file:
      with open(args.from_file, 'r') as f:
        session_data = json.load(f)

      # Validate required fields
      if 'name' not in session_data:
        print("❌ JSON file must contain 'name' field", file=sys.stderr)
        sys.exit(1)
      if 'assigned_users' not in session_data:
        print("❌ JSON file must contain 'assigned_users' field", file=sys.stderr)
        sys.exit(1)

    else:
      if not args.name:
        print('❌ Session name is required (--name)', file=sys.stderr)
        sys.exit(1)
      if not args.users:
        print('❌ At least one assigned user is required (--users)', file=sys.stderr)
        sys.exit(1)

      session_data = {'name': args.name, 'assigned_users': args.users}

      if args.description:
        session_data['description'] = args.description

    # Handle labeling schemas
    if args.schemas:
      # Validate requested schemas exist
      invalid_schemas = set(args.schemas) - available_schema_names
      if invalid_schemas:
        print(f'❌ Invalid schema names: {", ".join(invalid_schemas)}', file=sys.stderr)
        print(f'Available schemas: {", ".join(available_schema_names)}', file=sys.stderr)
        sys.exit(1)

      session_data['labeling_schemas'] = [{'name': name} for name in args.schemas]
    elif 'labeling_schemas' not in session_data:
      # Default to all available schemas
      session_data['labeling_schemas'] = [{'name': schema['name']} for schema in available_schemas]
    else:
      # Validate schemas from JSON file
      requested_schemas = {schema['name'] for schema in session_data.get('labeling_schemas', [])}
      invalid_schemas = requested_schemas - available_schema_names
      if invalid_schemas:
        print(f'❌ Invalid schema names in JSON: {", ".join(invalid_schemas)}', file=sys.stderr)
        print(f'Available schemas: {", ".join(available_schema_names)}', file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
      print('🔍 Dry run - would create the following labeling session:')
      print(json.dumps(session_data, indent=2))
      return

    # Create the labeling session
    result = await create_labeling_session(
      review_app_id=review_app_id, labeling_session_data=session_data
    )

    print('✅ Successfully created labeling session:')
    print(f'  Name: {result.get("name")}')
    print(f'  ID: {result.get("labeling_session_id")}')
    print(f'  MLflow Run ID: {result.get("mlflow_run_id")}')
    print(f'  Assigned Users: {", ".join(result.get("assigned_users", []))}')
    print(f'  Schemas: {", ".join([s["name"] for s in result.get("labeling_schemas", [])])}')

    if result.get('description'):
      print(f'  Description: {result.get("description")}')

    print('\n💡 Next steps:')
    print('  1. Link traces to this session using: uv run python tools/link_traces_to_session.py')
    print('  2. Open the session in Databricks for labeling')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
