#!/usr/bin/env python3
"""Update labeling schemas for a review app."""

import argparse
import asyncio
import json
import sys

from server.utils.review_apps_utils import review_apps_utils


async def main():
  """Update labeling schemas for a review app."""
  parser = argparse.ArgumentParser(
    description='Update labeling schemas for a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Update schema title
  python update_labeling_schemas.py review_app_id quality --title "Response Quality Assessment"

  # Update schema instruction
  python update_labeling_schemas.py review_app_id helpfulness --instruction "How helpful was this response to the user?"

  # Update numeric range
  python update_labeling_schemas.py review_app_id quality --min 0 --max 10

  # Update categorical options
  python update_labeling_schemas.py review_app_id helpfulness --options "Excellent" "Good" "Fair" "Poor"

  # Add option to categorical schema
  python update_labeling_schemas.py review_app_id helpfulness --add-option "Extremely Helpful"

  # Remove option from categorical schema
  python update_labeling_schemas.py review_app_id helpfulness --remove-option "Not Helpful"

  # Enable/disable comments
  python update_labeling_schemas.py review_app_id feedback --enable-comments
  python update_labeling_schemas.py review_app_id feedback --disable-comments

  # Update from JSON file
  python update_labeling_schemas.py review_app_id quality --from-file quality_update.json
        """,
  )

  parser.add_argument('review_app_id', help='Review app ID')
  parser.add_argument('schema_name', help='Name of the schema to update')

  # Update options
  parser.add_argument('--title', help='Update schema title')
  parser.add_argument('--instruction', help='Update schema instruction')
  parser.add_argument('--min', type=float, help='Update minimum value (numeric schemas only)')
  parser.add_argument('--max', type=float, help='Update maximum value (numeric schemas only)')
  parser.add_argument('--options', nargs='+', help='Replace all options (categorical schemas only)')
  parser.add_argument('--add-option', help='Add a new option (categorical schemas only)')
  parser.add_argument('--remove-option', help='Remove an option (categorical schemas only)')
  parser.add_argument('--enable-comments', action='store_true', help='Enable comment field')
  parser.add_argument('--disable-comments', action='store_true', help='Disable comment field')
  parser.add_argument('--from-file', help='Update schema from JSON file')

  # Options
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be updated without actually updating'
  )

  args = parser.parse_args()

  try:
    # Get current review app and schemas
    review_app = await review_apps_utils.get_review_app(args.review_app_id)
    current_schemas = review_app.get('labeling_schemas', [])

    # Find the schema to update
    schema_index = None
    target_schema = None
    for i, schema in enumerate(current_schemas):
      if schema['name'] == args.schema_name:
        schema_index = i
        target_schema = schema.copy()
        break

    if target_schema is None:
      print(f"❌ Schema '{args.schema_name}' not found", file=sys.stderr)
      available_names = [s['name'] for s in current_schemas]
      print(f'Available schemas: {", ".join(available_names)}', file=sys.stderr)
      sys.exit(1)

    # Track changes
    changes = []

    # Handle file input
    if args.from_file:
      with open(args.from_file, 'r') as f:
        file_updates = json.load(f)

      for key, value in file_updates.items():
        if key in target_schema and target_schema[key] != value:
          changes.append(f'  {key}: {target_schema[key]} → {value}')
          target_schema[key] = value

    # Handle individual updates
    if args.title:
      if target_schema.get('title') != args.title:
        changes.append(f'  title: {target_schema.get("title", "None")} → {args.title}')
        target_schema['title'] = args.title

    if args.instruction:
      if target_schema.get('instruction') != args.instruction:
        changes.append(
          f'  instruction: {target_schema.get("instruction", "None")} → {args.instruction}'
        )
        target_schema['instruction'] = args.instruction

    # Handle numeric updates
    if args.min is not None or args.max is not None:
      if 'numeric' not in target_schema:
        print(f"❌ Schema '{args.schema_name}' is not a numeric schema", file=sys.stderr)
        sys.exit(1)

      if args.min is not None:
        old_min = target_schema['numeric'].get('min_value', 'None')
        if old_min != args.min:
          changes.append(f'  min_value: {old_min} → {args.min}')
          target_schema['numeric']['min_value'] = args.min

      if args.max is not None:
        old_max = target_schema['numeric'].get('max_value', 'None')
        if old_max != args.max:
          changes.append(f'  max_value: {old_max} → {args.max}')
          target_schema['numeric']['max_value'] = args.max

    # Handle categorical updates
    if args.options or args.add_option or args.remove_option:
      if 'categorical' not in target_schema:
        print(f"❌ Schema '{args.schema_name}' is not a categorical schema", file=sys.stderr)
        sys.exit(1)

      current_options = target_schema['categorical'].get('options', [])

      if args.options:
        changes.append(f'  options: {current_options} → {args.options}')
        target_schema['categorical']['options'] = args.options

      if args.add_option:
        if args.add_option not in current_options:
          new_options = current_options + [args.add_option]
          changes.append(f'  add option: {args.add_option}')
          target_schema['categorical']['options'] = new_options
        else:
          print(f"⚠️  Option '{args.add_option}' already exists")

      if args.remove_option:
        if args.remove_option in current_options:
          new_options = [opt for opt in current_options if opt != args.remove_option]
          changes.append(f'  remove option: {args.remove_option}')
          target_schema['categorical']['options'] = new_options
        else:
          print(f"⚠️  Option '{args.remove_option}' not found")

    # Handle comment settings
    if args.enable_comments:
      if not target_schema.get('enable_comment', False):
        changes.append('  enable_comment: False → True')
        target_schema['enable_comment'] = True

    if args.disable_comments:
      if target_schema.get('enable_comment', False):
        changes.append('  enable_comment: True → False')
        target_schema['enable_comment'] = False

    # Check if any changes were made
    if not changes:
      print(f"ℹ️  No changes needed for schema '{args.schema_name}'")
      return

    if args.dry_run:
      print(f"🔍 Dry run - would update schema '{args.schema_name}':")
      print('Changes:')
      for change in changes:
        print(change)
      return

    # Update the schema in the list
    updated_schemas = current_schemas.copy()
    updated_schemas[schema_index] = target_schema

    # Update the review app
    update_data = {'labeling_schemas': updated_schemas}
    await review_apps_utils.update_review_app(
      review_app_id=args.review_app_id, review_app_data=update_data, update_mask='labeling_schemas'
    )

    print(f"✅ Successfully updated schema '{args.schema_name}':")
    for change in changes:
      print(change)

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
