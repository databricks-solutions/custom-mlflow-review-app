# MLflow Review App Development Guide

## Project Overview

This is a **production-ready MLflow Review App template** for evaluating AI agents and collecting human feedback on MLflow traces. It provides a complete infrastructure for:
- **Trace Evaluation**: Review and rate AI agent interactions
- **Custom Schemas**: Define evaluation criteria (ratings, categories, text feedback)
- **SME Workflows**: Assign subject matter experts to review sessions
- **Analytics**: Analyze feedback patterns and inter-rater agreement
- **MLflow Integration**: Direct connection to traces and experiments

## Quick Start for Customization

### 1. Initial Setup
```bash
./setup.sh                    # Interactive environment setup
./watch.sh                    # Start dev servers (frontend:5173, backend:8000)
```

### 2. Customize for Your Use Case

#### Option A: Automated Customization (Recommended)
Use the `/review-app` command in Claude Code for AI-guided setup:
```
/review-app [your experiment description]
```
This will:
- Analyze your MLflow experiment
- Suggest optimal labeling schemas
- Create tailored evaluation criteria
- Set up labeling sessions with appropriate filters

#### Option B: Manual Customization
1. **Update experiment in .env.local**:
   ```bash
   MLFLOW_EXPERIMENT_ID='your_experiment_id'
   SME_THANK_YOU_MESSAGE="Custom thank you message"
   ```

2. **Create custom labeling schemas**:
   ```bash
   ./mlflow-cli run create_labeling_schemas --help
   ```

3. **Set up labeling sessions**:
   ```bash
   ./mlflow-cli run create_labeling_session --help
   ```

### 3. Key Customization Points

#### Frontend Customization
- **`client/src/pages/LabelingPage.tsx`**: Main SME interface
- **`client/src/components/SMELabelingInterface.tsx`**: Core labeling UI
- **`client/src/components/session-renderer/`**: Custom trace renderers
- **`client/src/pages/DeveloperDashboard.tsx`**: Admin interface

#### Backend Customization
- **`server/routers/review/`**: Review app API endpoints
- **`server/routers/mlflow/`**: MLflow proxy endpoints
- **`server/utils/sme_*.py`**: SME analysis utilities
- **`server/models/`**: Data models and types

#### Custom Trace Renderers
Create specialized views for your traces:
```typescript
// client/src/components/session-renderer/renderers/CustomRenderer.tsx
export const CustomRenderer: ItemRenderer = {
  name: 'Custom View',
  description: 'Specialized view for your agent type',
  render: (item) => <YourCustomComponent item={item} />
};
```

## Tech Stack

**Backend:**
- Python with `uv` for package management
- FastAPI for API framework
- Databricks SDK for workspace integration
- MLflow SDK for trace and experiment management
- OpenAPI automatic client generation

**Frontend:**
- TypeScript with React
- Vite for fast development and hot reloading
- shadcn/ui components with Tailwind CSS
- React Query for API state management
- Bun for package management

## Development Workflow

### Package Management
- Use `uv add/remove` for Python dependencies, not manual edits to pyproject.toml
- Use `bun add/remove` for frontend dependencies, not manual package.json edits
- Always check if dependencies exist in the project before adding new ones

### Development Commands
- `./setup.sh` - Interactive environment setup and dependency installation
- `./watch.sh` - Start development servers with hot reloading (frontend:5173, backend:8000)
- `./fix.sh` - Format code (ruff for Python, prettier for TypeScript)
- `./deploy.sh` - Deploy to Databricks Apps

### 🚨 Development Server (CRITICAL) 🚨

**ALWAYS use the watch script - NEVER run servers manually:**

```bash
# Start development servers (REQUIRED COMMAND)
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &
```

**Why `./watch.sh` is required:**
- Configures environment variables properly
- Starts both frontend and backend correctly
- Generates TypeScript client automatically
- Handles authentication setup
- Provides proper logging and error handling

**Server Details:**
- **Frontend**: http://localhost:5173 (React + Vite)
- **Backend**: http://localhost:8000 (FastAPI)
- **API docs**: http://localhost:8000/docs
- **Hot reloading**: Both frontend and backend
- **Logs**: `/tmp/databricks-app-watch.log`

**Management Commands:**
- **Check logs**: `tail -f /tmp/databricks-app-watch.log`
- **Check status**: `ps aux | grep databricks-app` or check PID file
- **Stop servers**: `pkill -f "watch.sh"` or `kill $(cat /tmp/databricks-app-watch.pid)`

### 🚨 PYTHON EXECUTION RULE 🚨

**NEVER run `python` directly - ALWAYS use `uv run`:**

```bash
# ✅ CORRECT - Always use uv run
uv run python script.py
uv run uvicorn server.app:app
uv run scripts/make_fastapi_client.py

# ❌ WRONG - Never use python directly
python script.py
uvicorn server.app:app
python scripts/make_fastapi_client.py
```

### 🚨 DATABRICKS CLI EXECUTION RULE 🚨

**NEVER run `databricks` CLI directly - ALWAYS prefix with environment setup:**

```bash
# ✅ CORRECT - Always source .env.local and export variables first
source .env.local && export DATABRICKS_HOST && export DATABRICKS_CLIENT_ID && export DATABRICKS_CLIENT_SECRET && export DATABRICKS_WORKSPACE_ID && databricks current-user me

# ❌ WRONG - Never use databricks CLI directly
databricks current-user me
```

## Claude Natural Language Commands

Claude understands natural language commands routed through the unified CLI system:

### Development Lifecycle
- "start the devserver" → Runs `./watch.sh` in background with logging
- "kill the devserver" → Stops all background development processes
- "fix the code" → Runs `./fix.sh` to format Python and TypeScript code
- "deploy the app" → Runs `./deploy.sh` to deploy to Databricks Apps

### MLflow Operations (via unified CLI)
- "search traces" → `./mlflow-cli run search_traces`
- "analyze my experiment" → `./mlflow-cli run ai_analyze_experiment`
- "create labeling session" → `./mlflow-cli run create_labeling_session`
- "get experiment info" → `./mlflow-cli run get_experiment_info`

## 🚨 CRITICAL: Claude Tool Discovery Rules 🚨

**When users ask to modify review app state or want to know what tools are available:**

### Rule 1: Always Discover Available Tools First
```bash
# ALWAYS run this command first to see current tools
./mlflow-cli list
```

### Rule 2: For Review App State Modifications
When users ask to:
- Create, update, or delete labeling schemas
- Create, update, or delete labeling sessions
- Link traces to sessions
- Modify review app configuration
- Grant permissions or update settings

**ALWAYS start with tool discovery:**
```bash
./mlflow-cli list labeling    # For labeling-related requests
./mlflow-cli list mlflow      # For experiment/permission requests
./mlflow-cli search [keyword] # For specific functionality
```

### Rule 3: For "What tools are available?" requests
When users ask:
- "What tools do we have?"
- "Show me available commands"
- "What can I do with the CLI?"

**ALWAYS respond with:**
```bash
./mlflow-cli list             # Show all tools by category
```

This ensures you always have current tool information and can provide accurate recommendations.

### MLflow Tools via Unified CLI

**Always use the unified CLI system** - it's your primary interface for all MLflow operations:

```bash
# Discovery and help
./mlflow-cli list                    # List all available tools by category
./mlflow-cli list labeling          # List labeling tools only
./mlflow-cli search [query]         # Search tools by functionality
./mlflow-cli help [tool]            # Get detailed usage for any tool

# Execute tools (recommended approach)
./mlflow-cli run search_traces --limit 10
./mlflow-cli run create_labeling_session --name "review_session"
./mlflow-cli run get_experiment_info --experiment-id 12345
```

**Tool Categories:**
- **LABELING** (13 tools): Schema/session management, linking, analysis
- **TRACES** (5 tools): Search, metadata, analysis, URL generation  
- **MLFLOW** (5 tools): Experiment info, run management, permissions
- **ANALYTICS** (3 tools): AI-powered analysis and pattern detection
- **USER** (2 tools): Current user, workspace information
- **REVIEW-APPS** (1 tool): Review app management and configuration
- **LOGGING** (2 tools): MLflow feedback and expectation logging

**Advanced Usage (for scripting):**
```bash
# Direct tool access (when needed for automation)
uv run python tools/search_traces.py --limit 10
```

## 🎯 Claude Workflow for Review App Management

### When User Requests Review App Modifications:

1. **Discover Tools** (REQUIRED FIRST STEP):
   ```bash
   ./mlflow-cli list [category]  # Always check available tools first
   ```

2. **Get Tool Help**:
   ```bash
   ./mlflow-cli help [tool_name]  # Understand tool usage and options
   ```

3. **Execute Tool**:
   ```bash
   ./mlflow-cli run [tool_name] -- [tool_args]  # Run with proper arguments
   ```

### Example Workflows:

**Creating Labeling Schemas:**
```bash
# 1. Check labeling tools
./mlflow-cli list labeling

# 2. Get help for schema creation
./mlflow-cli help create_labeling_schemas

# 3. Create schemas
./mlflow-cli run create_labeling_schemas -- review_app_id --preset quality-helpfulness
```

**Managing Labeling Sessions:**
```bash
# 1. Check available session tools
./mlflow-cli search session

# 2. Get help for session creation
./mlflow-cli help create_labeling_session

# 3. Create session
./mlflow-cli run create_labeling_session -- review_app_id --name "Session Name"
```

### Slash Commands
Interactive commands for managing review app components:

- **`/review-app`** - Complete customization workflow
  - Analyzes your experiment
  - Suggests optimal configurations
  - Creates schemas and sessions
  - Deploys customized app

- **`/label-schemas`** - Manage labeling schemas
  - `/label-schemas` → List all schemas with visual representations
  - `/label-schemas add [description]` → Add new schema interactively
  - `/label-schemas modify [schema_name] [changes]` → Update existing schema
  - `/label-schemas delete [schema_name]` → Delete schema with confirmation

- **`/labeling-sessions`** - Manage labeling sessions  
  - `/labeling-sessions` → List all sessions with status and progress
  - `/labeling-sessions add [description]` → Create new session
  - `/labeling-sessions link [session_name] [trace_criteria]` → Link traces
  - `/labeling-sessions analyze [session_name]` → Statistical analysis

## Implementation Validation Workflow

**During implementation, ALWAYS:**
1. **Start development server first**: Use `./watch.sh`
2. **Open app with Playwright** to see current state
3. **After each implementation step:**
   - Check logs: `tail -f /tmp/databricks-app-watch.log`
   - Use Playwright to verify UI changes
   - Test user interactions and API calls
4. **FastAPI Endpoint Verification**: After adding ANY new endpoint, curl test it
5. **Iterative validation**: Test each feature before moving to next step

## API Development Best Practices

### Type Safety
- Use proper Pydantic models instead of Dict[str, Any]
- Define clear request/response models
- Leverage FastAPI's automatic validation

### Error Handling
- Custom exceptions in `server/exceptions.py`
- Automatic conversion to JSON responses
- Frontend toast notifications via error middleware

### React Query Integration
- All API calls use React Query hooks
- `useQuery` for GET requests
- `useMutation` for POST/PUT/DELETE
- Automatic cache invalidation

## MLflow Integration Details

### Architecture Overview
```
MLflow Experiment
  └── Traces (AI agent interactions)
       └── Review App (defines evaluation framework)
            └── Labeling Sessions (organize review batches)
                 └── Labeling Items (individual trace reviews)
```

### Key Concepts
1. **Trace Linking**: We link traces to sessions, not copy them
2. **Session Backing**: Each labeling session has an MLflow run ID
3. **Schema Flexibility**: Mix ratings, categories, and text feedback
4. **User Assignment**: Automatic permission management via MLflow SDK

### API Endpoints
- **MLflow Proxies** (`/api/mlflow/*`): Direct MLflow API access
- **Review Apps** (`/api/review-apps/*`): Evaluation framework management
- **Labeling Sessions** (`/api/review-apps/{id}/labeling-sessions/*`): Session CRUD
- **Labeling Items** (`/api/review-apps/{id}/labeling-sessions/{id}/items/*`): Review tracking

## Deployment

### Deploy to Databricks Apps
```bash
./deploy.sh                  # Deploy existing app
./deploy.sh --create        # Create and deploy new app
./deploy.sh --verbose       # Deploy with detailed logging
```

### 🚨 CRITICAL: Post-Deployment Verification 🚨

**ALWAYS perform these verification steps after deployment - DO NOT SKIP!**

#### Step 1: Check Deployment Logs (REQUIRED)
```bash
# Get app URL first
uv run python app_status.py --format json | jq -r '.app_status.url'

# Monitor logs for startup (replace with your app URL)
uv run python dba_logz.py https://your-app.databricksapps.com --search "INFO" --duration 60
```

**What to look for:**
- ✅ `"INFO: Uvicorn running on http://0.0.0.0:8000"` - Server started
- ✅ `"INFO: Application startup complete"` - App ready
- ❌ `"ERROR"` or `"CRITICAL"` - Check for failures
- ❌ `"ModuleNotFoundError"` - Missing dependencies

**If Uvicorn doesn't start within 2 minutes:**
- Keep checking logs - deployment can take 3-5 minutes
- Look for import errors or missing dependencies
- Check requirements.txt was generated correctly

#### Step 2: Test API Health (REQUIRED)
```bash
# Test health endpoint
uv run python dba_client.py https://your-app.databricksapps.com /health

# Expected response:
# {"status": "healthy"}
```

**If health check fails:**
- Server may still be starting - wait and retry
- Check logs for startup errors
- Verify app.yaml configuration

#### Step 3: Verify API Documentation (REQUIRED)
```bash
# Test API docs endpoint
uv run python dba_client.py https://your-app.databricksapps.com /docs

# Should return HTML content starting with:
# <!DOCTYPE html>
# <html>
# <head>
#     <link type="text/css" rel="stylesheet" href="...swagger-ui...">
```

**If /docs fails:**
- FastAPI may have startup errors
- Check for router registration issues
- Verify all imports in server/app.py

#### Step 4: Test Core API Endpoints
```bash
# Test current user endpoint
uv run python dba_client.py https://your-app.databricksapps.com /api/user/me

# Test review app endpoint
uv run python dba_client.py https://your-app.databricksapps.com /api/review-apps/current

# Test configuration endpoint
uv run python dba_client.py https://your-app.databricksapps.com /api/config
```

#### Step 5: Monitor Continuous Logs
```bash
# Keep monitoring for any runtime errors
uv run python dba_logz.py https://your-app.databricksapps.com --search "ERROR" --duration 120

# Check for successful requests
uv run python dba_logz.py https://your-app.databricksapps.com --search "GET /api" --duration 60
```

### Common Deployment Issues & Solutions

| Issue | Detection | Solution |
|-------|-----------|----------|
| **Uvicorn won't start** | No "Uvicorn running" in logs | Check requirements.txt, verify all imports |
| **Import errors** | `ModuleNotFoundError` in logs | Add missing package to pyproject.toml, redeploy |
| **Static files 404** | UI doesn't load | Verify client/build exists, check app.py static mount |
| **API routes 404** | `/api/*` returns 404 | Check router registration in server/app.py |
| **Auth failures** | 401/403 errors | Verify DATABRICKS_TOKEN in app environment |
| **Slow startup** | Takes >5 minutes | Normal for first deploy, check logs for progress |

### Deployment Debugging Commands

```bash
# Full app status with permissions
uv run python app_status.py --verbose

# Get app logs (browser authentication required)
# Visit in browser: https://your-app.databricksapps.com/logz

# Test specific API endpoint with full response
uv run python dba_client.py https://your-app.databricksapps.com /api/health --verbose

# Check workspace files were uploaded
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN
databricks workspace list "$DBA_SOURCE_CODE_PATH"
```

### 🔄 Redeployment After Fixes

If you need to fix issues and redeploy:
```bash
# 1. Fix the issue locally
# 2. Test locally first
./run_app_local.sh

# 3. Redeploy
./deploy.sh --verbose

# 4. Repeat verification steps above
```

**IMPORTANT**: Never assume deployment succeeded without verification! Always check logs and test endpoints.

## Troubleshooting

### Common Issues

#### Development Server Issues
```bash
# Check logs
tail -f /tmp/databricks-app-watch.log

# Restart servers
pkill -f watch.sh
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &
```

#### TypeScript Client Missing
```bash
uv run python scripts/make_fastapi_client.py
```

#### Authentication Issues
```bash
# Test authentication
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks current-user me

# Reconfigure if needed
./setup.sh
```

## Session Renderer System

Create custom views for different trace types:

### Built-in Renderers
- **Default**: Conversation-style chat view
- **Compact Timeline**: Condensed timeline view

### Creating Custom Renderers
See `client/src/session-renderer/README.md` for complete guide:
1. Create renderer component in `renderers/`
2. Register in `renderers/index.ts`
3. Set via MLflow run tags or UI selector

### Example Custom Renderer
```typescript
export const AnalyticsRenderer: ItemRenderer = {
  name: 'Analytics View',
  description: 'View for analytical agent traces',
  render: (item) => <AnalyticsView trace={item.source} />
};
```

## Best Practices

### Code Quality
- Run `./fix.sh` before commits
- Use TypeScript strictly - no `any` types
- Follow existing patterns in codebase
- Write self-documenting code

### Performance
- Use React Query for all API calls
- Implement pagination for large datasets
- Use virtual scrolling for long lists
- Profile with middleware tools

### Security
- Never commit secrets or tokens
- Use environment variables for config
- Validate all user inputs
- Follow OWASP best practices

### Testing
- Test API endpoints via FastAPI docs
- Use Playwright for UI testing
- Check network tab for API issues
- Verify with multiple user roles

## Key Files Reference

### Configuration
- `.env` - Default environment variables (checked into git)
- `.env.local` - Local environment variables (git-ignored, overrides .env)
- `app.yaml` - Databricks Apps deployment config

### Backend
- `server/app.py` - FastAPI application entry
- `server/routers/` - API endpoint routers
- `server/models/` - Pydantic data models
- `server/utils/` - Utility functions

### Frontend
- `client/src/App.tsx` - React app entry
- `client/src/pages/` - Page components
- `client/src/components/` - Reusable components
- `client/src/hooks/` - Custom React hooks

### Tools & Scripts
- `tools/` - CLI tools for MLflow operations
- `scripts/` - Development automation
- `cli.py` - Unified CLI interface
- `mlflow-cli` - Convenient CLI wrapper

Remember: This is a production-ready template focused on rapid customization and deployment for MLflow trace evaluation workflows.