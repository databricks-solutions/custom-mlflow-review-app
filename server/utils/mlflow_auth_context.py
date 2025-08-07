"""MLflow authentication context management for OBO support."""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv

from server.utils.auth_context import AuthContext

# Load environment variables
load_dotenv()


@contextmanager
def mlflow_auth_context(auth_context: Optional[AuthContext] = None) -> Generator[None, None, None]:
  """Context manager that temporarily sets up MLflow authentication.

  Args:
      auth_context: Optional auth context with OBO token support

  Yields:
      None - Use within context to make MLflow API calls with proper auth

  Example:
      with mlflow_auth_context(request_auth_context):
          # MLflow operations here will use the OBO token
          session = labeling.create_labeling_session(...)
  """
  # Store original environment
  original_token = os.environ.get('DATABRICKS_TOKEN')
  original_host = os.environ.get('DATABRICKS_HOST')

  try:
    if auth_context:
      # Set environment variables for MLflow to use
      if auth_context.token:
        os.environ['DATABRICKS_TOKEN'] = auth_context.token

      host = auth_context.get_databricks_host()
      if host:
        os.environ['DATABRICKS_HOST'] = host

    yield

  finally:
    # Restore original environment
    if original_token is not None:
      os.environ['DATABRICKS_TOKEN'] = original_token
    elif 'DATABRICKS_TOKEN' in os.environ:
      del os.environ['DATABRICKS_TOKEN']

    if original_host is not None:
      os.environ['DATABRICKS_HOST'] = original_host
    elif 'DATABRICKS_HOST' in os.environ:
      del os.environ['DATABRICKS_HOST']


def setup_mlflow_for_obo(auth_context: Optional[AuthContext] = None) -> None:
  """Set up MLflow configuration to use OBO token if available.

  This is a simpler alternative to the context manager for cases where
  you want to set up auth once at the beginning of an operation.

  Args:
      auth_context: Optional auth context with OBO token support
  """
  if auth_context and auth_context.token:
    # Set the token as environment variable for MLflow to pick up
    os.environ['DATABRICKS_TOKEN'] = auth_context.token

    # Set host if available
    host = auth_context.get_databricks_host()
    if host:
      os.environ['DATABRICKS_HOST'] = host
