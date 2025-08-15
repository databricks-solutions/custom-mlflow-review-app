#!/usr/bin/env python3
"""List Model Serving Endpoints Tool

List all available Databricks model serving endpoints in the workspace.
"""

import argparse
import json
import os
import sys

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError


def list_endpoints(format_output: str = 'table') -> None:
  """List all model serving endpoints in the workspace.

  Args:
      format_output: Output format ('table', 'json', 'names')
  """
  try:
    client = WorkspaceClient()
    endpoints = list(client.serving_endpoints.list())

    if not endpoints:
      print('No model serving endpoints found in this workspace.')
      return

    if format_output == 'json':
      # Output simplified JSON for setup
      endpoint_data = []
      for endpoint in endpoints:
        # Extract ready status from state
        if endpoint.state and hasattr(endpoint.state, 'ready'):
          state = str(endpoint.state.ready).split('.')[-1] if endpoint.state.ready else 'UNKNOWN'
        else:
          state = 'UNKNOWN'

        endpoint_data.append(
          {'name': endpoint.name, 'state': state, 'creator': endpoint.creator or 'N/A'}
        )
      print(json.dumps(endpoint_data, indent=2))

    elif format_output == 'names':
      # Output just endpoint names
      for endpoint in endpoints:
        print(endpoint.name)

    else:  # table format (default)
      print(f'{"NAME":<40} {"STATE":<15} {"CREATOR":<30} {"LAST UPDATED"}')
      print('-' * 100)

      for endpoint in endpoints:
        name = endpoint.name[:39] if len(endpoint.name) > 39 else endpoint.name
        # Extract ready status from state
        if endpoint.state and hasattr(endpoint.state, 'ready'):
          state = str(endpoint.state.ready).split('.')[-1] if endpoint.state.ready else 'UNKNOWN'
        else:
          state = 'UNKNOWN'
        creator = (
          endpoint.creator[:29]
          if endpoint.creator and len(endpoint.creator) > 29
          else (endpoint.creator or 'N/A')
        )
        last_updated = (
          str(endpoint.last_updated_timestamp) if endpoint.last_updated_timestamp else 'N/A'
        )

        print(f'{name:<40} {state:<15} {creator:<30} {last_updated}')

    if format_output == 'table':
      print(f'\nTotal endpoints: {len(endpoints)}')

  except DatabricksError as e:
    print(f'❌ Databricks API error: {e}', file=sys.stderr)
    sys.exit(1)
  except Exception as e:
    print(f'❌ Error listing endpoints: {e}', file=sys.stderr)
    sys.exit(1)


def main():
  parser = argparse.ArgumentParser(
    description='List all Databricks model serving endpoints',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # List endpoints in table format (default)
  python tools/list_model_endpoints.py
  
  # List endpoints as JSON with full details
  python tools/list_model_endpoints.py --format json
  
  # List only endpoint names
  python tools/list_model_endpoints.py --format names
        """,
  )

  parser.add_argument(
    '--format',
    choices=['table', 'json', 'names'],
    default='table',
    help='Output format (default: table)',
  )

  args = parser.parse_args()

  list_endpoints(args.format)


if __name__ == '__main__':
  main()
