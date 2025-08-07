#!/usr/bin/env python3
"""Test script to query Databricks table using Spark SQL with serverless compute."""

import os

from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession


def create_spark_session():
  """Create a Spark session connected to Databricks serverless."""
  try:
    # Use Databricks Connect for serverless compute
    spark = DatabricksSession.builder.serverless().getOrCreate()
    return spark
  except Exception as e:
    print(f'Failed to create Databricks serverless session: {e}')
    print('Falling back to local Spark session...')

    # Fallback to local Spark session
    spark = (
      SparkSession.builder.appName('DatabricksTableTest')
      .config('spark.sql.adaptive.enabled', 'true')
      .config('spark.sql.adaptive.coalescePartitions.enabled', 'true')
      .getOrCreate()
    )
    return spark


def query_trace_logs():
  """Query the first row from the trace_logs table."""
  table_name = 'mosaic_catalog.lilac_schema.trace_logs_2639312608800919'

  print('Connecting to Databricks serverless compute...')
  spark = create_spark_session()

  try:
    print(f'Querying table: {table_name}')
    print('=' * 60)

    # Query the first row
    query = f'SELECT * FROM {table_name} LIMIT 1'
    print(f'SQL Query: {query}')
    print()

    # Execute the query
    df = spark.sql(query)

    # Show the schema
    print('Table Schema:')
    print('-' * 40)
    df.printSchema()
    print()

    # Show the first row
    print('First Row Data:')
    print('-' * 40)
    rows = df.collect()

    if rows:
      row = rows[0]
      print(f'Number of columns: {len(row)}')
      print()

      # Print each column and its value
      for i, (field, value) in enumerate(zip(df.schema.fields, row)):
        print(f'Column {i + 1}: {field.name}')
        print(f'  Type: {field.dataType}')
        print(f'  Value: {value}')
        print(f'  Value Type: {type(value)}')
        print()
    else:
      print('No data found in the table.')

    # Get row count
    try:
      count = spark.sql(f'SELECT COUNT(*) as count FROM {table_name}').collect()[0]['count']
      print(f'Total rows in table: {count:,}')
    except Exception as e:
      print(f'Could not get row count: {e}')

  except Exception as e:
    print(f'Error querying table: {e}')
    print('\nTrying to list available tables in the schema...')

    try:
      # List tables in the schema
      tables_df = spark.sql('SHOW TABLES IN mosaic_catalog.lilac_schema')
      print('Available tables in mosaic_catalog.lilac_schema:')
      tables_df.show(truncate=False)
    except Exception as schema_e:
      print(f'Could not list tables in schema: {schema_e}')

      try:
        # List schemas in the catalog
        schemas_df = spark.sql('SHOW SCHEMAS IN mosaic_catalog')
        print('Available schemas in mosaic_catalog:')
        schemas_df.show(truncate=False)
      except Exception as catalog_e:
        print(f'Could not list schemas in catalog: {catalog_e}')

  finally:
    spark.stop()


if __name__ == '__main__':
  print('Databricks Spark SQL Test Script')
  print('=' * 60)

  # Check environment variables
  print('Environment check:')
  print(f'DATABRICKS_HOST: {"✓" if os.getenv("DATABRICKS_HOST") else "✗"}')
  print(f'DATABRICKS_TOKEN: {"✓" if os.getenv("DATABRICKS_TOKEN") else "✗"}')
  print(f'DATABRICKS_CONFIG_PROFILE: {os.getenv("DATABRICKS_CONFIG_PROFILE", "Not set")}')
  print()

  try:
    query_trace_logs()
  except KeyboardInterrupt:
    print('\nScript interrupted by user.')
  except Exception as e:
    print(f'Unexpected error: {e}')
