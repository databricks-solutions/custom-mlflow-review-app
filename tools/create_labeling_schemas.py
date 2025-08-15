#!/usr/bin/env python3
"""Create labeling schemas for a review app."""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List

from server.utils.review_apps_utils import review_apps_utils
from tools.utils.review_app_resolver import resolve_review_app_id


def create_numeric_schema(
  name: str,
  title: str,
  instruction: str,
  min_val: float = 1.0,
  max_val: float = 5.0,
  enable_comment: bool = False,
  schema_type: str = 'FEEDBACK',
) -> Dict[str, Any]:
  """Create a numeric (rating) labeling schema."""
  return {
    'name': name,
    'type': schema_type,
    'title': title,
    'instruction': instruction,
    'enable_comment': enable_comment,
    'numeric': {'min_value': min_val, 'max_value': max_val},
  }


def create_categorical_schema(
  name: str,
  title: str,
  instruction: str,
  options: List[str],
  enable_comment: bool = False,
  schema_type: str = 'FEEDBACK',
) -> Dict[str, Any]:
  """Create a categorical (multiple choice) labeling schema."""
  return {
    'name': name,
    'type': schema_type,
    'title': title,
    'instruction': instruction,
    'enable_comment': enable_comment,
    'categorical': {'options': options},
  }


def create_text_schema(
  name: str, title: str, instruction: str, schema_type: str = 'FEEDBACK'
) -> Dict[str, Any]:
  """Create a text (open-ended) labeling schema."""
  return {
    'name': name,
    'type': schema_type,
    'title': title,
    'instruction': instruction,
    'enable_comment': True,
    'text': {},
  }


async def main():
  """Create labeling schemas for a review app."""
  parser = argparse.ArgumentParser(
    description='Create labeling schemas for a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Create a single numeric rating schema (uses current experiment)
  python create_labeling_schemas.py --numeric quality "Response Quality" "Rate the quality of the AI response" --min 1 --max 5

  # Create with specific review app ID
  python create_labeling_schemas.py review_app_id --categorical helpfulness "Helpfulness" "Was the response helpful?" --options "Very Helpful" "Somewhat Helpful" "Not Helpful"

  # Create with specific experiment ID
  python create_labeling_schemas.py --experiment-id exp123 --text feedback "General Feedback" "Provide any additional feedback"

  # Create multiple schemas from JSON file
  python create_labeling_schemas.py --from-file schemas.json

  # Use preset template
  python create_labeling_schemas.py --preset quality-helpfulness
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')

  # Schema creation options
  schema_group = parser.add_mutually_exclusive_group(required=True)

  # Numeric schema
  schema_group.add_argument(
    '--numeric',
    nargs=3,
    metavar=('NAME', 'TITLE', 'INSTRUCTION'),
    help='Create numeric rating schema: name title instruction',
  )
  parser.add_argument(
    '--min', type=float, default=1.0, help='Minimum value for numeric schema (default: 1.0)'
  )
  parser.add_argument(
    '--max', type=float, default=5.0, help='Maximum value for numeric schema (default: 5.0)'
  )

  # Categorical schema
  schema_group.add_argument(
    '--categorical',
    nargs=3,
    metavar=('NAME', 'TITLE', 'INSTRUCTION'),
    help='Create categorical schema: name title instruction',
  )
  parser.add_argument('--options', nargs='+', help='Options for categorical schema')

  # Text schema
  schema_group.add_argument(
    '--text',
    nargs=3,
    metavar=('NAME', 'TITLE', 'INSTRUCTION'),
    help='Create text feedback schema: name title instruction',
  )

  # File input
  schema_group.add_argument('--from-file', help='Create schemas from JSON file')

  # Preset templates
  schema_group.add_argument(
    '--preset',
    choices=['quality-helpfulness', 'ai-evaluation', 'content-review'],
    help='Use preset schema templates',
  )

  # Common options
  parser.add_argument(
    '--enable-comment', action='store_true', help='Enable comment field for schema'
  )
  parser.add_argument(
    '--schema-type',
    choices=['FEEDBACK', 'EXPECTATION'],
    default='FEEDBACK',
    help='Schema type: FEEDBACK for evaluating responses, EXPECTATION for defining criteria (default: FEEDBACK)',
  )
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be created without actually creating'
  )

  args = parser.parse_args()

  try:
    # Resolve review app ID
    review_app_id, current_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )

    # Get fresh data from API to avoid cache issues
    current_app = await review_apps_utils.get_review_app(review_app_id)
    current_schemas = current_app.get('labeling_schemas', [])
    current_schema_names = {schema['name'] for schema in current_schemas}

    # Build new schemas based on arguments
    new_schemas = []

    if args.numeric:
      name, title, instruction = args.numeric
      if name in current_schema_names:
        print(f"❌ Schema '{name}' already exists", file=sys.stderr)
        sys.exit(1)
      new_schemas.append(
        create_numeric_schema(
          name, title, instruction, args.min, args.max, args.enable_comment, args.schema_type
        )
      )

    elif args.categorical:
      if not args.options:
        print('❌ --options required for categorical schema', file=sys.stderr)
        sys.exit(1)
      name, title, instruction = args.categorical
      if name in current_schema_names:
        print(f"❌ Schema '{name}' already exists", file=sys.stderr)
        sys.exit(1)
      new_schemas.append(
        create_categorical_schema(
          name, title, instruction, args.options, args.enable_comment, args.schema_type
        )
      )

    elif args.text:
      name, title, instruction = args.text
      if name in current_schema_names:
        print(f"❌ Schema '{name}' already exists", file=sys.stderr)
        sys.exit(1)
      new_schemas.append(create_text_schema(name, title, instruction, args.schema_type))

    elif args.from_file:
      with open(args.from_file, 'r') as f:
        file_schemas = json.load(f)
      for schema in file_schemas:
        if schema['name'] in current_schema_names:
          print(f"❌ Schema '{schema['name']}' already exists", file=sys.stderr)
          sys.exit(1)
      new_schemas.extend(file_schemas)

    elif args.preset:
      if args.preset == 'quality-helpfulness':
        new_schemas = [
          create_numeric_schema(
            'quality', 'Quality Rating', 'Rate the overall quality of the response', 1.0, 5.0
          ),
          create_categorical_schema(
            'helpfulness',
            'Helpfulness',
            'How helpful was the response?',
            ['Very Helpful', 'Somewhat Helpful', 'Not Helpful'],
          ),
        ]
      elif args.preset == 'ai-evaluation':
        new_schemas = [
          create_numeric_schema('accuracy', 'Accuracy', 'How accurate is the response?', 1.0, 5.0),
          create_numeric_schema(
            'relevance', 'Relevance', 'How relevant is the response to the query?', 1.0, 5.0
          ),
          create_categorical_schema(
            'safety',
            'Safety',
            'Is the response safe and appropriate?',
            ['Safe', 'Potentially Harmful', 'Harmful'],
          ),
          create_text_schema(
            'feedback', 'Additional Feedback', 'Provide any additional feedback or comments'
          ),
        ]
      elif args.preset == 'content-review':
        new_schemas = [
          create_categorical_schema(
            'approval',
            'Content Approval',
            'Should this content be approved?',
            ['Approve', 'Needs Review', 'Reject'],
          ),
          create_categorical_schema(
            'category',
            'Content Category',
            'What category does this content belong to?',
            ['Educational', 'Entertainment', 'Informational', 'Commercial', 'Other'],
          ),
          create_text_schema('notes', 'Review Notes', 'Add any notes about this content'),
        ]

      # Check for conflicts
      for schema in new_schemas:
        if schema['name'] in current_schema_names:
          print(f"❌ Schema '{schema['name']}' already exists", file=sys.stderr)
          sys.exit(1)

    if args.dry_run:
      print('🔍 Dry run - would create the following schemas:')
      print(json.dumps(new_schemas, indent=2))
      return

    # Add new schemas to existing ones
    updated_schemas = current_schemas + new_schemas

    # Update the review app
    update_data = {'labeling_schemas': updated_schemas}
    await review_apps_utils.update_review_app(
      review_app_id=review_app_id, review_app_data=update_data, update_mask='labeling_schemas'
    )

    print('✅ Successfully created labeling schemas:')
    for schema in new_schemas:
      print(f'  - {schema["name"]} ({schema.get("title", "No title")})')

    print(f'\nTotal schemas in review app: {len(updated_schemas)}')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
