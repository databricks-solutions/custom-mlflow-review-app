# Technical Design Document
## Custom MLflow Review App Template

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│ Databricks MLflow   │
│  (TanStack Query)│    │  (Proxy + Logic) │    │ (Tracking Server)   │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
         ↓                       ↓                          ↓
   Client Caching          Stateless Design          Single Workspace
   Auto-generated         Bearer Token Auth         Experiments/Traces
     TS Client            Low-level Proxies          Review Apps/Sessions
```

### Technology Stack

**Backend:**
- **FastAPI**: Modern Python web framework with automatic OpenAPI generation
- **Databricks SDK**: Official SDK for MLflow and workspace integration
- **Pydantic**: Data validation and serialization
- **httpx**: Async HTTP client for proxying requests
- **uv**: Fast Python package management

**Frontend:**
- **React 18**: UI framework with TypeScript
- **TanStack Query**: Client-side caching and state management
- **shadcn/ui**: Pre-built accessible components
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool and dev server
- **Bun**: JavaScript runtime and package manager

**Authentication:**
- App service principal (default)
- Configurable via `/custom-review-app` command
- Bearer token passed to all Databricks API calls

### Libraries and Frameworks

**Python Dependencies (Backend):**
```python
# Core
fastapi = "^0.104.1"
uvicorn = "^0.24.0"
pydantic = "^2.5.0"
httpx = "^0.25.2"

# Databricks Integration
databricks-sdk = "^0.59.0"
mlflow-skinny = "^3.1.1"

# Utilities
python-dotenv = "^1.0.0"
rich = "^14.0.0"
```

**JavaScript Dependencies (Frontend):**
```json
// Core
"react": "^18.2.0",
"react-dom": "^18.2.0",
"@tanstack/react-query": "^5.0.0",

// UI Components
"@radix-ui/*": "latest",
"tailwindcss": "^3.3.0",
"class-variance-authority": "^0.7.0",

// Utilities
"axios": "^1.6.0",
"lucide-react": "^0.292.0"
```

### Data Architecture

**MLflow Integration:**
1. **Experiments**: Single experiment per review app instance
2. **Traces**: Conversation data fetched via `search_traces` API
3. **Runs**: Each labeling session is an MLflow run
4. **Label Schemas**: Stored in review app configuration

**Data Flow:**
```
User Request → FastAPI → Databricks API → MLflow Data
     ↓             ↓              ↓              ↓
   React UI    Validation    Auth Headers    Response
     ↓             ↓              ↓              ↓
TanStack Query  Transform    Service Principal  JSON
```

**No Local Storage:**
- All data persisted in MLflow
- No database required
- Stateless backend design
- Client-side caching only

### Integration Points

**1. MLflow Proxy Endpoints:**
```python
# Low-level proxy pattern
POST   /api/mlflow/search-traces
GET    /api/mlflow/experiments/{experiment_id}
GET    /api/mlflow/runs/{run_id}
POST   /api/mlflow/runs/create
POST   /api/mlflow/traces/link-to-run
```

**2. Review App Management:**
```python
# Managed Evals APIs
GET    /api/review-apps?filter=experiment_id={id}
POST   /api/review-apps
PATCH  /api/review-apps/{review_app_id}
```

**3. Labeling Session APIs:**
```python
# Session management
GET    /api/review-apps/{id}/labeling-sessions
POST   /api/review-apps/{id}/labeling-sessions
PATCH  /api/review-apps/{id}/labeling-sessions/{session_id}
DELETE /api/review-apps/{id}/labeling-sessions/{session_id}
```

**4. Session Items APIs:**
```python
# Item management
GET    /api/review-apps/{id}/labeling-sessions/{sid}/items
POST   /api/review-apps/{id}/labeling-sessions/{sid}/items:batchCreate
GET    /api/labeling-sessions/{sid}/next-uncompleted-item
```

### API Design Patterns

**1. Authentication Utility:**
```python
# server/utils/databricks_auth.py
async def get_databricks_headers() -> dict:
    """Get auth headers using app service principal"""
    return {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
```

**2. Proxy Pattern:**
```python
# Generic proxy for Databricks APIs
async def proxy_databricks_api(
    method: str,
    path: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None
) -> dict:
    """Proxy requests to Databricks with auth"""
```

**3. Error Handling:**
```python
# User-friendly errors for SMEs
class UserFriendlyException(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details
```

### Real-time Updates

**Polling Strategy (No WebSockets):**
- Frontend polls for updates every 5-10 seconds
- TanStack Query handles deduplication
- Conditional fetching based on user activity
- Background refetch for progress tracking

## Implementation Plan

### Phase 1: Core Backend Infrastructure
**Week 1-2: Foundation**

1. **Databricks Authentication Utility**
   - Create `server/utils/databricks_auth.py`
   - Service principal token management
   - Request header generation
   - Error handling wrapper

2. **MLflow Proxy Endpoints**
   - `/api/mlflow/search-traces` with pagination
   - `/api/mlflow/experiments/{id}` 
   - `/api/mlflow/runs/*` endpoints
   - Generic proxy utility

3. **Review App APIs**
   - List review apps by experiment
   - Create review app
   - Update review app (PATCH)
   - Label schema management

4. **Testing Infrastructure**
   - curl test scripts for each endpoint
   - Use experiment 2178582188830602
   - Verify with Postman/HTTPie

### Phase 2: Session Management
**Week 3-4: Core Features**

5. **Labeling Session APIs**
   - List sessions with hydration
   - Create new sessions
   - Update session metadata
   - Delete sessions
   - Batch operations

6. **Session Items Management**
   - List items with pagination
   - Batch create items
   - Get next uncompleted item
   - Update item state
   - Trace hydration

7. **Frontend Foundation**
   - Replace WelcomePage
   - Session list view
   - Basic review interface
   - TanStack Query setup

### Phase 3: Review Interface
**Week 5-6: User Experience**

8. **SME Review Interface**
   - Conversation display (left panel)
   - Dynamic question forms (right panel)
   - Progress tracking
   - Auto-advance logic
   - Navigation controls

9. **Developer Dashboard (/dev)**
   - Session management UI
   - Trace search interface
   - Progress analytics
   - Bulk operations

10. **Polish & Testing**
    - Error boundaries
    - Loading states
    - Responsive design
    - E2E testing

## Development Workflow

### API Development Process
1. **Define Pydantic models** for request/response
2. **Create endpoint** in appropriate router
3. **Test with curl** immediately
4. **Update OpenAPI** client generation
5. **Implement frontend** consumption

### Testing Strategy
```bash
# Test each endpoint as built
curl -X GET http://localhost:8000/api/mlflow/search-traces \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "max_results": 10}'

# Verify in API docs
open http://localhost:8000/docs
```

### Code Organization
```
server/
├── routers/
│   ├── mlflow.py      # MLflow proxy endpoints
│   ├── review_apps.py # Review app management
│   ├── sessions.py    # Labeling sessions
│   └── items.py       # Session items
├── utils/
│   ├── databricks_auth.py
│   ├── proxy.py
│   └── errors.py
└── models/
    ├── traces.py
    ├── review_apps.py
    └── sessions.py
```

### Deployment Considerations
- Environment variables for auth
- CORS configuration for frontend
- Rate limiting for API calls
- Health check endpoints
- Logging and monitoring

## Next Steps

1. **Immediate**: Create auth utility and first endpoint
2. **Today**: Implement search_traces with full testing
3. **This Week**: Complete all MLflow proxy endpoints
4. **Next Week**: Build review app management APIs
5. **Following Week**: Implement full UI with customization

The architecture is designed for maximum flexibility while maintaining simplicity. Every decision supports the goal of making customization easy for users via Claude assistance.