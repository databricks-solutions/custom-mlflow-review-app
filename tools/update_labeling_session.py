#!/usr/bin/env python3
"""Update a labeling session for a review app."""

import argparse
import asyncio
import json
import sys

from server.utils.labeling_sessions_utils import get_labeling_session, update_labeling_session
from tools.utils.review_app_resolver import resolve_review_app_id


async def main():
  """Update a labeling session for a review app."""
  parser = argparse.ArgumentParser(
    description='Update a labeling session for a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Update session name (uses current experiment)
  python update_labeling_session.py session_id --name "New Session Name"

  # Update with specific review app ID
  python update_labeling_session.py review_app_id session_id --users user1@example.com user2@example.com

  # Update with specific experiment ID
  python update_labeling_session.py --experiment-id exp123 session_id --add-user newuser@example.com

  # Remove a user from assigned users
  python update_labeling_session.py session_id --remove-user olduser@example.com

  # Update description
  python update_labeling_session.py session_id --description "Updated description"

  # Update labeling schemas
  python update_labeling_session.py session_id --schemas quality_rating helpfulness

  # Add a schema to existing schemas
  python update_labeling_session.py session_id --add-schema feedback

  # Remove a schema from existing schemas
  python update_labeling_session.py session_id --remove-schema helpfulness

  # Update from JSON file
  python update_labeling_session.py session_id --from-file session_update.json
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('session_id', help='Labeling session ID to update')

  # Update options
  parser.add_argument('--name', help='Update session name')
  parser.add_argument('--description', help='Update session description')
  parser.add_argument('--users', nargs='+', help='Replace all assigned users')
  parser.add_argument('--add-user', help='Add a user to assigned users')
  parser.add_argument('--remove-user', help='Remove a user from assigned users')
  parser.add_argument('--schemas', nargs='+', help='Replace all labeling schemas')
  parser.add_argument('--add-schema', help='Add a schema to labeling schemas')
  parser.add_argument('--remove-schema', help='Remove a schema from labeling schemas')
  parser.add_argument('--from-file', help='Update session from JSON file')

  # Options
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be updated without actually updating'
  )

  args = parser.parse_args()

  try:
    # Resolve review app ID
    review_app_id, review_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )

    # Get current session
    current_session = await get_labeling_session(
      review_app_id=review_app_id, labeling_session_id=args.session_id
    )
    available_schemas = review_app.get('labeling_schemas', [])
    available_schema_names = {schema['name'] for schema in available_schemas}

    # Track changes and build update data
    changes = []
    update_data = {}
    update_fields = []

    # Handle file input
    if args.from_file:
      with open(args.from_file, 'r') as f:
        file_updates = json.load(f)

      for key, value in file_updates.items():
        if key in current_session and current_session[key] != value:
          changes.append(f'  {key}: {current_session[key]} → {value}')
          update_data[key] = value
          update_fields.append(key)

    # Handle individual updates
    if args.name:
      if current_session.get('name') != args.name:
        changes.append(f'  name: {current_session.get("name", "None")} → {args.name}')
        update_data['name'] = args.name
        update_fields.append('name')

    if args.description is not None:  # Allow empty string
      if current_session.get('description') != args.description:
        changes.append(
          f'  description: {current_session.get("description", "None")} → {args.description}'
        )
        update_data['description'] = args.description
        update_fields.append('description')

    # Handle user updates
    current_users = current_session.get('assigned_users', [])
    updated_users = current_users.copy()

    if args.users:
      changes.append(f'  assigned_users: {current_users} → {args.users}')
      updated_users = args.users

    if args.add_user:
      if args.add_user not in updated_users:
        updated_users.append(args.add_user)
        changes.append(f'  add user: {args.add_user}')
      else:
        print(f"⚠️  User '{args.add_user}' already assigned to session")

    if args.remove_user:
      if args.remove_user in updated_users:
        updated_users.remove(args.remove_user)
        changes.append(f'  remove user: {args.remove_user}')
      else:
        print(f"⚠️  User '{args.remove_user}' not found in assigned users")

    if updated_users != current_users:
      update_data['assigned_users'] = updated_users
      update_fields.append('assigned_users')

    # Handle schema updates
    current_schemas = [s['name'] for s in current_session.get('labeling_schemas', [])]
    updated_schemas = current_schemas.copy()

    if args.schemas:
      # Validate requested schemas exist
      invalid_schemas = set(args.schemas) - available_schema_names
      if invalid_schemas:
        print(f'❌ Invalid schema names: {", ".join(invalid_schemas)}', file=sys.stderr)
        print(f'Available schemas: {", ".join(available_schema_names)}', file=sys.stderr)
        sys.exit(1)

      changes.append(f'  labeling_schemas: {current_schemas} → {args.schemas}')
      updated_schemas = args.schemas

    if args.add_schema:
      if args.add_schema not in available_schema_names:
        print(f"❌ Schema '{args.add_schema}' not found", file=sys.stderr)
        print(f'Available schemas: {", ".join(available_schema_names)}', file=sys.stderr)
        sys.exit(1)

      if args.add_schema not in updated_schemas:
        updated_schemas.append(args.add_schema)
        changes.append(f'  add schema: {args.add_schema}')
      else:
        print(f"⚠️  Schema '{args.add_schema}' already in session")

    if args.remove_schema:
      if args.remove_schema in updated_schemas:
        updated_schemas.remove(args.remove_schema)
        changes.append(f'  remove schema: {args.remove_schema}')
      else:
        print(f"⚠️  Schema '{args.remove_schema}' not found in session")

    if updated_schemas != current_schemas:
      update_data['labeling_schemas'] = [{'name': name} for name in updated_schemas]
      update_fields.append('labeling_schemas')

    # Check if any changes were made
    if not changes:
      print(f"ℹ️  No changes needed for session '{current_session.get('name', args.session_id)}'")
      return

    if args.dry_run:
      print(f"🔍 Dry run - would update session '{current_session.get('name', args.session_id)}':")
      print('Changes:')
      for change in changes:
        print(change)
      print(f'\nUpdate mask: {",".join(update_fields)}')
      return

    # Update the session
    result = await update_labeling_session(
      review_app_id=review_app_id,
      labeling_session_id=args.session_id,
      labeling_session_data=update_data,
      update_mask=','.join(update_fields),
    )

    print(f"✅ Successfully updated session '{result.get('name', args.session_id)}':")
    for change in changes:
      print(change)

    # Show updated session summary
    print('\n📋 **Updated Session Summary:**')
    print(f'  Name: {result.get("name", "N/A")}')
    print(f'  ID: {result.get("labeling_session_id", "N/A")}')
    print(f'  Assigned Users: {", ".join(result.get("assigned_users", []))}')
    print(f'  Schemas: {", ".join([s["name"] for s in result.get("labeling_schemas", [])])}')
    if result.get('description'):
      print(f'  Description: {result.get("description")}')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
