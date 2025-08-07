# Integration Tests

This directory contains integration tests for the MLflow Review App, focusing on testing the complete system including:

## Test Categories

### Authentication Tests (`test_auth_integration.py`)
- OBO (On-Behalf-Of) authentication flow
- Token propagation through middleware
- Auth context creation and usage
- Service principal vs user authentication

### API Integration Tests (`test_api_integration.py`)
- FastAPI endpoints with real Databricks connections
- MLflow API proxy functionality
- Review app and labeling session workflows
- Cross-service API calls

### OBO End-to-End Tests (`test_obo_e2e.py`)
- Complete OBO workflow from client to database
- User identity extraction and validation
- Permission propagation
- Real vs simulated OBO scenarios

### Database Integration Tests (`test_db_integration.py`)
- Databricks SQL connections with OBO tokens
- MLflow tracking with user identity
- Unity Catalog permissions with OBO

## Running Integration Tests

### Prerequisites
```bash
# Ensure environment is configured
source .env.local
export DATABRICKS_HOST
export DATABRICKS_TOKEN

# Install test dependencies
uv add pytest pytest-asyncio httpx
```

### Running Tests
```bash
# Run all integration tests
uv run pytest integration_tests/

# Run specific test file
uv run pytest integration_tests/test_obo_e2e.py

# Run with verbose output
uv run pytest integration_tests/ -v

# Run specific test
uv run pytest integration_tests/test_auth_integration.py::test_obo_token_propagation -v
```

### Test Configuration
Integration tests use:
- Live Databricks workspace connections
- Real MLflow experiments and traces
- Actual authentication tokens
- Production app endpoints (when deployed)

### Environment Variables Required
- `DATABRICKS_HOST`: Workspace URL
- `DATABRICKS_TOKEN`: Access token for testing
- `DATABRICKS_HTTP_PATH`: SQL warehouse path (optional)
- `TEST_EXPERIMENT_ID`: MLflow experiment for testing (optional)

## Test Structure

Each test file follows the pattern:
```python
import pytest
from server.utils.auth_context import AuthContext
from integration_tests.fixtures import *

class TestAuthIntegration:
    def test_obo_flow(self, auth_context, live_app_url):
        # Test implementation
        pass
```

## Fixtures

Common fixtures are defined in `fixtures.py`:
- `auth_context`: Configured AuthContext for testing
- `live_app_url`: URL of deployed Databricks app
- `test_client`: FastAPI test client
- `obo_token`: Simulated OBO token for testing