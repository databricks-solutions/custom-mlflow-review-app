#!/usr/bin/env python3
"""Delete labeling schemas from a review app."""

import argparse
import asyncio
import sys

from server.utils.review_apps_utils import review_apps_utils
from tools.utils.review_app_resolver import resolve_review_app_id


async def main():
  """Delete labeling schemas from a review app."""
  parser = argparse.ArgumentParser(
    description='Delete labeling schemas from a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Delete a single schema (uses current experiment)
  python delete_labeling_schemas.py quality

  # Delete with specific review app ID
  python delete_labeling_schemas.py review_app_id quality helpfulness feedback

  # Delete with specific experiment ID
  python delete_labeling_schemas.py --experiment-id exp123 --all

  # Show what would be deleted without actually deleting
  python delete_labeling_schemas.py quality --dry-run
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('schema_names', nargs='*', help='Names of schemas to delete')
  parser.add_argument('--all', action='store_true', help='Delete ALL schemas (use with caution)')
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be deleted without actually deleting'
  )
  parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

  args = parser.parse_args()

  # Validate arguments
  if not args.all and not args.schema_names:
    print('❌ Specify schema names to delete or use --all flag', file=sys.stderr)
    sys.exit(1)

  if args.all and args.schema_names:
    print('❌ Cannot specify both --all and individual schema names', file=sys.stderr)
    sys.exit(1)

  try:
    # Resolve review app ID and get current review app and schemas
    review_app_id, review_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )
    current_schemas = review_app.get('labeling_schemas', [])

    if not current_schemas:
      print('ℹ️  No schemas found in review app')
      return

    # Determine schemas to delete
    if args.all:
      schemas_to_delete = current_schemas.copy()
      schemas_to_keep = []
    else:
      # Find schemas to delete
      schemas_to_delete = []
      schemas_to_keep = []

      current_schema_names = {schema['name']: schema for schema in current_schemas}

      # Check if requested schemas exist
      missing_schemas = set(args.schema_names) - set(current_schema_names.keys())
      if missing_schemas:
        print(f'❌ Schema(s) not found: {", ".join(missing_schemas)}', file=sys.stderr)
        available_names = list(current_schema_names.keys())
        print(f'Available schemas: {", ".join(available_names)}', file=sys.stderr)
        sys.exit(1)

      # Separate schemas to delete and keep
      for schema in current_schemas:
        if schema['name'] in args.schema_names:
          schemas_to_delete.append(schema)
        else:
          schemas_to_keep.append(schema)

    # Show what will be deleted
    print(f'🗑️  **Schemas to be deleted ({len(schemas_to_delete)}):**')
    for schema in schemas_to_delete:
      name = schema.get('name', 'Unnamed')
      title = schema.get('title', 'No title')
      schema_type = (
        'numeric' if 'numeric' in schema else 'categorical' if 'categorical' in schema else 'text'
      )
      print(f'  - {name} ({title}) [{schema_type}]')

    if schemas_to_keep:
      print(f'\n📋 **Schemas to be kept ({len(schemas_to_keep)}):**')
      for schema in schemas_to_keep:
        name = schema.get('name', 'Unnamed')
        title = schema.get('title', 'No title')
        print(f'  - {name} ({title})')
    else:
      print('\n⚠️  **WARNING: This will delete ALL schemas from the review app!**')

    if args.dry_run:
      print('\n🔍 Dry run - no changes made')
      return

    # Confirmation
    if not args.force:
      if len(schemas_to_delete) == 1:
        schema_name = schemas_to_delete[0]['name']
        confirmation_phrase = f'delete {schema_name}'
      elif args.all:
        confirmation_phrase = 'delete all schemas'
      else:
        confirmation_phrase = 'delete these schemas'

      print('\n⚠️  **This action cannot be undone!**')
      print(f'To proceed, type: **{confirmation_phrase}**')
      user_input = input('Confirmation: ').strip()

      if user_input != confirmation_phrase:
        print('❌ Confirmation failed. No changes made.')
        return

    # Perform deletion by updating with remaining schemas
    update_data = {'labeling_schemas': schemas_to_keep}
    await review_apps_utils.update_review_app(
      review_app_id=review_app_id, review_app_data=update_data, update_mask='labeling_schemas'
    )

    # Success message
    print(f'\n✅ Successfully deleted {len(schemas_to_delete)} schema(s):')
    for schema in schemas_to_delete:
      print(f'  - {schema["name"]}')

    if schemas_to_keep:
      print(f'\nRemaining schemas: {len(schemas_to_keep)}')
    else:
      print('\n⚠️  Review app now has no labeling schemas')
      print('💡 Create new schemas with: uv run python tools/create_labeling_schemas.py')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
