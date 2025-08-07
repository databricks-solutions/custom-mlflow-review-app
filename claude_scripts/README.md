# Claude Scripts

This folder contains test scripts created by Claude for testing functionality and exploring the codebase.

## Purpose

Claude creates scripts in this folder to:
- Test database connections and queries
- Validate API endpoints and functionality
- Explore data structures and schemas
- Debug issues and verify implementations
- Prototype new features before integration

## Current Scripts

### `test_spark_query.py`
Tests Databricks table access using Spark SQL with serverless compute.
- Connects to Databricks using serverless compute
- Queries the first row from a specified table
- Displays schema information and data
- Includes fallback error handling and table exploration

### `test_sql_query.py`
Tests Databricks table access using SQL warehouses.
- Uses Databricks SDK for SQL warehouse connections
- Executes SQL queries through warehouse endpoints
- Displays results and schema information
- Includes warehouse management and error handling

## Usage

These scripts are designed to be run from the project root directory:

```bash
# Run with uv (recommended)
uv run claude_scripts/test_spark_query.py
uv run claude_scripts/test_sql_query.py

# Or with python directly
python claude_scripts/test_spark_query.py
python claude_scripts/test_sql_query.py
```

## Requirements

Scripts in this folder may require:
- Databricks authentication (token or profile)
- Specific Python dependencies (automatically handled by uv)
- Access to Databricks resources (warehouses, clusters, tables)

## Note

These scripts are for testing and exploration purposes. They should not be used in production environments.