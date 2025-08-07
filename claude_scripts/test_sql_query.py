#!/usr/bin/env python3
"""Test script to execute SQL queries using Databricks SQL warehouses."""

import os
import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def execute_sql_query(sql_query):
  """Execute a SQL query using Databricks SQL warehouse."""
  print('Connecting to Databricks workspace...')

  try:
    # Initialize Databricks client
    client = WorkspaceClient()

    # List available SQL warehouses
    print('Available SQL warehouses:')
    warehouses = list(client.warehouses.list())

    if not warehouses:
      print('No SQL warehouses found. Please create a SQL warehouse first.')
      return

    # Use the first available warehouse
    warehouse = warehouses[0]
    print(f'Using warehouse: {warehouse.name} (ID: {warehouse.id})')
    print(f'Warehouse state: {warehouse.state}')
    print()

    # Start the warehouse if it's not running
    if warehouse.state.value != 'RUNNING':
      print('Starting warehouse...')
      client.warehouses.start(warehouse.id)
      print('Warehouse started.')
      print()

    # Execute the provided SQL query
    print(f'SQL Query: {sql_query}')
    print('=' * 60)

    # Execute the query
    response = client.statement_execution.execute_statement(
      warehouse_id=warehouse.id, statement=sql_query, wait_timeout='30s'
    )

    print(f'Statement ID: {response.statement_id}')

    # Check if status is available before accessing its attributes
    if response.status and response.status.state:
      print(f'Status: {response.status.state}')

      if response.status.state == StatementState.SUCCEEDED:
        print('\nQuery executed successfully!')

        # Print schema information
        if response.manifest and response.manifest.schema:
          print('\nResult Schema:')
          print('-' * 40)
          for i, column in enumerate(response.manifest.schema.columns):
            print(f'Column {i + 1}: {column.name} ({column.type_name})')
          print()

        # Print result data
        if response.result and response.result.data_array:
          print('Query Results:')
          print('-' * 40)

          # Print column headers
          if response.manifest and response.manifest.schema:
            headers = [col.name for col in response.manifest.schema.columns]
            print(' | '.join(headers))
            print('-' * (len(' | '.join(headers))))

          # Print data rows
          for row in response.result.data_array:
            print(' | '.join(str(val) if val is not None else 'NULL' for val in row))

          print(f'\nTotal rows returned: {len(response.result.data_array)}')

        else:
          print('No data returned from query.')

      else:
        print(f'Query failed with status: {response.status.state}')
        if response.status.error:
          print(f'Error: {response.status.error}')
    else:
      print('No status information available from response.')

  except Exception as e:
    print(f'Error executing query: {e}')


if __name__ == '__main__':
  print('Databricks SQL Query Executor')
  print('=' * 60)

  # Check for SQL query argument
  if len(sys.argv) != 2:
    print('Usage: python test_sql_query.py "<SQL_QUERY>"')
    print('\nExample:')
    print('python test_sql_query.py "SELECT * FROM my_table LIMIT 10"')
    sys.exit(1)

  sql_query = sys.argv[1]

  # Check environment variables
  print('Environment check:')
  print(f'DATABRICKS_HOST: {"✓" if os.getenv("DATABRICKS_HOST") else "✗"}')
  print(f'DATABRICKS_TOKEN: {"✓" if os.getenv("DATABRICKS_TOKEN") else "✗"}')
  print(f'DATABRICKS_CONFIG_PROFILE: {os.getenv("DATABRICKS_CONFIG_PROFILE", "Not set")}')
  print()

  try:
    execute_sql_query(sql_query)
  except KeyboardInterrupt:
    print('\nScript interrupted by user.')
  except Exception as e:
    print(f'Unexpected error: {e}')
