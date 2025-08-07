# Backend API Summary

This document summarizes all the implemented backend APIs for the Custom MLflow Review App template.

## Base URL
All API endpoints are prefixed with `/api` when accessed through the FastAPI server.

## Authentication
All endpoints use Bearer token authentication via the `DATABRICKS_TOKEN` environment variable.

## Implemented Endpoints

### 1. User Endpoints
- `GET /api/user/me` - Get current user information
- `GET /api/user/me/workspace` - Get user and workspace information

### 2. MLflow Endpoints (Low-level Proxies)
- `GET /api/mlflow/experiments/{experiment_id}` - Get experiment details
- `GET /api/mlflow/runs/{run_id}` - Get run details  
- `POST /api/mlflow/runs/create` - Create a new run
- `POST /api/mlflow/runs/update` - Update a run
- `POST /api/mlflow/runs/search` - Search for runs
- `POST /api/mlflow/traces/link-to-run` - Link traces to a run (for adding traces to labeling sessions)
- `GET /api/mlflow/traces/{trace_id}` - Get trace information
- `GET /api/mlflow/traces/{trace_id}/data` - Get trace data (spans)

**Note**: The `search_traces` endpoint is not available as a direct API - it's SDK-only functionality.

### 3. Review Apps Endpoints
- `GET /api/review-apps` - List review apps (supports filtering by experiment_id)
- `POST /api/review-apps` - Create a new review app
- `GET /api/review-apps/{review_app_id}` - Get specific review app
- `PATCH /api/review-apps/{review_app_id}` - Update review app (requires update_mask)

**Note**: DELETE endpoint is not supported by the Databricks API.

### 4. Labeling Sessions Endpoints
- `GET /api/review-apps/{review_app_id}/labeling-sessions` - List labeling sessions
- `POST /api/review-apps/{review_app_id}/labeling-sessions` - Create labeling session
- `GET /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}` - Get specific session
- `PATCH /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}` - Update session
- `DELETE /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}` - Delete session

### 5. Labeling Items Endpoints
- `GET /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items` - List items
- `GET /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}` - Get item
- `PATCH /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}` - Update item

**Note**: Item creation and deletion are not supported via API. Items are typically created through other mechanisms.

### 6. Health Check
- `GET /health` - Health check endpoint

## Example Usage

### Create a Review App
```bash
curl -X POST "http://localhost:8000/api/review-apps" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "2178582188830602",
    "labeling_schemas": [
      {
        "name": "quality",
        "type": "FEEDBACK",
        "title": "Response Quality",
        "numeric": {
          "min_value": 1,
          "max_value": 5
        }
      }
    ]
  }'
```

### Create a Labeling Session
```bash
curl -X POST "http://localhost:8000/api/review-apps/{review_app_id}/labeling-sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Labeling Session",
    "assigned_users": ["user@example.com"],
    "labeling_schemas": [
      {"name": "quality"}
    ]
  }'
```

### Link Traces to a Labeling Session
```bash
# First get the mlflow_run_id from the labeling session
# Then link traces to that run
curl -X POST "http://localhost:8000/api/mlflow/traces/link-to-run" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "37ce7bf46ed34137be5caa18cd7e7a8d",
    "trace_ids": ["trace-id-1", "trace-id-2"]
  }'
```

## TypeScript Client

The TypeScript client is automatically generated from the OpenAPI spec and provides type-safe access to all endpoints:

```typescript
import { apiClient } from '@/fastapi_client';

// Get review apps
const apps = await apiClient.reviewApps.listReviewApps({
  filter: 'experiment_id=2178582188830602'
});

// Create labeling session
const session = await apiClient.labelingSessions.createLabelingSession({
  reviewAppId: 'app-id',
  requestBody: {
    name: 'My Session',
    assigned_users: ['user@example.com']
  }
});
```

## Notes

1. All endpoints use the low-level proxy pattern for maximum flexibility
2. Response models are defined in `server/models/review_apps.py`
3. The backend handles authentication automatically via environment variables
4. Empty responses from Databricks API are normalized to expected structures
5. CSRF tokens are only needed for ajax-api endpoints (not currently used)