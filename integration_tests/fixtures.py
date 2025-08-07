"""Common fixtures for integration tests."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from dba_client import DatabricksAppClient
from server.app import app
from server.utils.auth_context import AuthContext


@pytest.fixture
def auth_context() -> AuthContext:
  """Create AuthContext for testing."""
  return AuthContext.from_env()


@pytest.fixture
def obo_auth_context() -> AuthContext:
  """Create OBO AuthContext for testing."""
  token = os.getenv('DATABRICKS_TOKEN')
  if not token:
    pytest.skip('DATABRICKS_TOKEN not available for OBO testing')
  return AuthContext.from_obo_token(token)


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
  """Create FastAPI test client."""
  with TestClient(app) as client:
    yield client


@pytest.fixture
def live_app_url() -> str:
  """Get live Databricks app URL."""
  return 'https://custom-mlflow-review-app-5722066275360235.aws.databricksapps.com'


@pytest.fixture
def dba_client(live_app_url: str) -> DatabricksAppClient:
  """Create DatabricksAppClient for testing."""
  return DatabricksAppClient(live_app_url, obo=False)


@pytest.fixture
def dba_client_obo(live_app_url: str) -> DatabricksAppClient:
  """Create DatabricksAppClient with OBO for testing."""
  return DatabricksAppClient(live_app_url, obo=True)


@pytest.fixture
def databricks_host() -> str:
  """Get Databricks host from environment."""
  host = os.getenv('DATABRICKS_HOST')
  if not host:
    pytest.skip('DATABRICKS_HOST not configured')
  return host


@pytest.fixture
def experiment_id() -> str:
  """Get test experiment ID."""
  exp_id = os.getenv('TEST_EXPERIMENT_ID') or '2178582188830602'
  return exp_id


@pytest.fixture
def databricks_token() -> str:
  """Get Databricks token for testing."""
  token = os.getenv('DATABRICKS_TOKEN')
  if not token:
    pytest.skip('DATABRICKS_TOKEN not available')
  return token
