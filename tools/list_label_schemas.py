#!/usr/bin/env python3
"""List labeling schemas for a review app."""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.utils.review_app_resolver import resolve_review_app_id

console = Console()


def format_schema(schema: Dict[str, Any]) -> str:
  """Format a single schema for display."""
  lines = []

  # Schema type badge
  schema_type = schema.get('type', 'FEEDBACK')
  type_badge = '📝 FEEDBACK' if schema_type == 'FEEDBACK' else '🎯 EXPECTATION'

  lines.append(f'{type_badge}')
  lines.append(f'Name: {schema.get("name", "N/A")}')
  lines.append(f'Title: {schema.get("title", "N/A")}')
  lines.append(f'Instruction: {schema.get("instruction", "N/A")}')

  # Show schema details based on type
  if 'numeric' in schema:
    numeric = schema['numeric']
    lines.append(
      f'Type: Numeric Rating ({numeric.get("min_value", 1)}-{numeric.get("max_value", 5)})'
    )
  elif 'categorical' in schema:
    categorical = schema['categorical']
    options = categorical.get('options', [])
    lines.append('Type: Categorical')
    lines.append(f'Options: {", ".join(options)}')
  elif 'text' in schema:
    lines.append('Type: Text Input')

  if schema.get('enable_comment'):
    lines.append('💬 Comments enabled')

  return '\n'.join(lines)


async def main():
  """List labeling schemas for a review app."""
  parser = argparse.ArgumentParser(
    description='List labeling schemas for a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # List schemas for current experiment's review app
  python list_labeling_schemas.py
  
  # List schemas for specific review app
  python list_labeling_schemas.py review_app_id
  
  # List schemas for specific experiment
  python list_labeling_schemas.py --experiment-id exp123
  
  # Output as JSON
  python list_labeling_schemas.py --json
  
  # Show only schema names
  python list_labeling_schemas.py --names-only
    """,
  )

  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('--json', action='store_true', help='Output as JSON')
  parser.add_argument('--names-only', action='store_true', help='Show only schema names')

  args = parser.parse_args()

  try:
    # Resolve review app ID
    review_app_id, current_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )
    
    # Get latest data directly from the API to avoid caching issues
    from server.utils.review_apps_utils import review_apps_utils
    review_app_data = await review_apps_utils.get_review_app(review_app_id)
    
    schemas = review_app_data.get('labeling_schemas', [])

    if not schemas:
      console.print('📋 No labeling schemas found for this review app', style='yellow')
      console.print('\nCreate schemas with: ./mlflow-cli run create_labeling_schemas --help')
      return

    # Output based on format preference
    if args.json:
      print(json.dumps(schemas, indent=2))
    elif args.names_only:
      for schema in schemas:
        print(schema.get('name', 'N/A'))
    else:
      # Rich formatted output
      console.print('\n📋 [bold]Labeling Schemas for Review App[/bold]')
      console.print(f'Review App ID: {review_app_id}')
      console.print(f'Total schemas: {len(schemas)}\n')

      # Create a table for overview
      table = Table(show_header=True, header_style='bold magenta')
      table.add_column('Name', style='cyan')
      table.add_column('Type', style='green')
      table.add_column('Schema Type', style='yellow')
      table.add_column('Title')
      table.add_column('Comments', style='blue')

      for schema in schemas:
        # Determine schema input type
        if 'numeric' in schema:
          input_type = f'Rating ({schema["numeric"]["min_value"]}-{schema["numeric"]["max_value"]})'
        elif 'categorical' in schema:
          input_type = f'Choice ({len(schema["categorical"]["options"])} options)'
        elif 'text' in schema:
          input_type = 'Text'
        else:
          input_type = 'Unknown'

        schema_type = schema.get('type', 'FEEDBACK')
        comments = '✓' if schema.get('enable_comment') else '✗'

        table.add_row(
          schema.get('name', 'N/A'), input_type, schema_type, schema.get('title', 'N/A'), comments
        )

      console.print(table)

      # Show detailed view
      console.print('\n[bold]Detailed Schema Definitions:[/bold]\n')

      for i, schema in enumerate(schemas, 1):
        panel_content = format_schema(schema)
        console.print(
          Panel(
            panel_content,
            title=f'[bold cyan]{i}. {schema.get("name", "N/A")}[/bold cyan]',
            border_style='blue',
          )
        )
        if i < len(schemas):
          console.print()

      # Show usage tips
      console.print('\n💡 [dim]Tips:[/dim]')
      console.print('[dim]• To update schemas: ./mlflow-cli run update_labeling_schemas[/dim]')
      console.print('[dim]• To delete schemas: ./mlflow-cli run delete_labeling_schemas[/dim]')
      console.print('[dim]• To create schemas: ./mlflow-cli run create_labeling_schemas[/dim]')

  except Exception as e:
    console.print(f'❌ Error: {str(e)}', style='red')
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
