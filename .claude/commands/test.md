---
name: test
description: Comprehensive QA testing of MLflow Review App workflows
---

# MLflow Review App QA Testing

This command performs comprehensive QA testing of both developer and SME workflows in the MLflow Review App using Playwright MCP for realistic user interaction.

## Test Scenario: Customer Support Agent Evaluation

## Test Sections

### Available Test Sections:
- **environment** - Development server setup and health checks
- **dashboard** - Developer dashboard UI and API testing
- **sessions** - Labeling session CRUD operations
- **traces** - Trace search and linking functionality
- **schemas** - Labeling schema management
- **labeling** - Subject matter expert labeling interface
- **verification** - End-to-end label verification

## Test Workflow (English Instructions Only)

When you run `/test`, I will guide you through testing the MLflow Review App using step-by-step English instructions. Each test section verifies a different part of the application workflow.

### 1. Environment Testing
**Goal**: Verify development environment is properly set up and functional

**What I'll check:**
- Confirm `.env.local` exists with Databricks credentials
- Verify development server is running on ports 5173 (frontend) and 8000 (backend) 
- If server not running, I'll start it with `nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &`
- Test API health endpoints to ensure backend is responding
- Verify API config endpoint returns valid experiment_id from config.yaml
- Check that Databricks authentication is working

**Success Criteria:**
- ✅ Environment file exists and is configured
- ✅ Frontend and backend servers respond to health checks
- ✅ API returns configuration with valid experiment_id
- ✅ Databricks authentication working

### 2. Developer Dashboard Testing  
**Goal**: Validate developer interface displays correctly and APIs work

**What I'll do:**
- Open developer dashboard at `http://localhost:5173/dev` using Playwright browser automation
- Take screenshot to verify UI loaded properly with no errors
- Test review apps API endpoint with current experiment_id from config
- Verify review app configuration displays correctly in the UI
- Check that experiment details and user information are shown
- Test navigation between different dashboard sections

**Success Criteria:**
- ✅ Dashboard UI loads without JavaScript errors
- ✅ Current user information displays correctly  
- ✅ Experiment configuration shows with proper experiment_id
- ✅ Review apps are listed (if any exist for the experiment)
- ✅ Navigation between sections works properly

### 3. Labeling Sessions Testing
**Goal**: Test session viewing and management UI (read-only unless explicitly requested)

**What I'll do:**
- List existing labeling sessions via API to see current state
- Use Playwright to view session management interface
- **IMPORTANT**: I will NOT create, modify, or delete any existing sessions unless you explicitly ask
- If you want me to test session creation, I'll ask for confirmation first
- Test session details view for existing sessions  
- Verify session data displays correctly in the UI
- Confirm proper MLflow run_id links are shown

**Success Criteria:**
- ✅ Session listing loads and displays existing sessions correctly
- ✅ Session details view works for existing sessions
- ✅ Session data integrity is maintained (no modifications)
- ✅ UI displays session information accurately
- ✅ MLflow run_id links are properly shown

### 4. Trace Management Testing
**Goal**: Verify trace search and display functionality (read-only)

**What I'll do:**
- Search for traces using the unified CLI: `./mlflow-cli run search_traces --limit 5`
- Test various search filters (status, timestamps, tags) to ensure search works
- Verify trace details can be retrieved for individual traces
- **IMPORTANT**: I will NOT link traces to sessions or modify any trace data unless you explicitly ask
- If you want me to test trace linking, I'll ask for confirmation first
- Verify trace metadata and content display correctly in the UI
- Test trace viewing in existing sessions (read-only)

**Success Criteria:**
- ✅ Trace search returns results from the experiment
- ✅ Individual trace details are accessible  
- ✅ Trace data integrity is maintained (no linking unless requested)
- ✅ Existing trace-session links display correctly
- ✅ Trace content displays properly with all metadata

### 5. Schema Configuration Testing  
**Goal**: Test labeling schema viewing and validation (read-only unless explicitly requested)

**What I'll do:**
- Retrieve current review app labeling schemas via API
- **IMPORTANT**: I will NOT modify, add, or delete any existing schemas unless you explicitly ask
- If you want me to test schema modifications, I'll ask for confirmation first
- Verify schemas display correctly in the UI
- Test schema viewing functionality across the application
- Validate that existing schema configurations are properly formatted

**Success Criteria:**
- ✅ Current schemas retrieved successfully from API
- ✅ Schema data integrity is maintained (no modifications unless requested)
- ✅ Schemas display correctly in the UI
- ✅ Schema viewing functionality works properly
- ✅ Existing schema configurations are valid and well-formed

### 6. Subject Matter Expert Labeling Interface Testing
**Goal**: Test the end-user labeling experience (view-only unless explicitly requested)

**What I'll do:**
- Navigate to main labeling interface at `http://localhost:5173/`
- View existing labeling sessions and their current state
- **IMPORTANT**: I will NOT submit any labels or modify existing label data unless you explicitly ask
- If you want me to test label submission, I'll ask for confirmation first
- Verify labeling questions display correctly based on configured schemas
- Test UI functionality (form controls, navigation) without submitting data
- Check that existing labels display correctly if any exist

**Success Criteria:**
- ✅ Labeling interface loads properly without errors
- ✅ Session selection works and shows available sessions
- ✅ Labeling questions match the configured schemas
- ✅ Label input controls display and function correctly (without submitting)
- ✅ Existing labels display correctly if present
- ✅ Navigation between traces works properly

### 7. End-to-End Verification Testing
**Goal**: Verify complete workflow integrity and data consistency (read-only verification)

**What I'll do:**
- Verify existing data consistency across the system
- Check labeling session items API shows correct status for existing items
- Test that existing labels can be retrieved via trace search APIs
- Verify data integrity and proper formatting of existing data
- Test any export/reporting functionality if available (read-only)
- **IMPORTANT**: This is verification-only - no data creation or modification
- Confirm the complete workflow displays correctly: trace → session → labels → verification

**Success Criteria:**
- ✅ Existing data is consistent and accessible
- ✅ Session status tracking is accurate for existing sessions
- ✅ Existing labels are retrievable via API queries
- ✅ Data integrity is maintained throughout the system
- ✅ Complete workflow displays and functions correctly

## How I'll Handle Issues

If any test step fails, I will:

1. **Identify the specific problem** with detailed error analysis
2. **Check common failure points**:
   - Development server not running → Guide you through `./watch.sh` startup
   - Authentication issues → Help verify `.env.local` and token validity  
   - No traces found → Check experiment_id and MLflow setup
   - UI not loading → Look for JavaScript errors and port conflicts
   - API errors → Test endpoints manually with curl commands

3. **Provide manual verification steps** you can run:
   ```bash
   # Check development server status
   ps aux | grep -E "(vite|uvicorn|watch.sh)"
   curl -s http://localhost:8000/health | jq
   curl -s http://localhost:5173
   
   # Test API endpoints manually  
   curl -s http://localhost:8000/api/config | jq
   ./mlflow-cli run get_current_user
   ./mlflow-cli run search_traces --limit 3
   
   # Open UIs in browser
   open http://localhost:5173/dev      # Developer dashboard
   open http://localhost:5173/         # Labeling interface
   ```

4. **Ask if you want guidance** on fixing the specific issues found

## Key Testing Benefits

- **Comprehensive Coverage**: Tests entire user journey from dev setup to production labeling
- **Real UI Testing**: Uses Playwright for actual user interactions 
- **API Validation**: Confirms all backend functionality works correctly
- **Data Integrity**: Verifies end-to-end data flow and persistence
- **Clear Guidance**: Provides step-by-step instructions and troubleshooting

## What Gets Validated

### API Endpoints:
- `GET /api/config` - Configuration and experiment_id
- `GET /api/review-apps` - Review app listing and filtering
- `GET/POST /api/review-apps/{id}/labeling-sessions` - Session management
- `POST /api/mlflow/search-traces` - Trace discovery and filtering
- `POST /api/mlflow/traces/link-to-run` - Trace linking to sessions
- `GET /api/review-apps/{id}/labeling-sessions/{id}/items` - Labeling items
- `PATCH /api/review-apps/{id}` - Schema configuration updates

### UI Components:
- Developer dashboard loading and navigation
- Review app configuration display
- Labeling session creation dialogs  
- Session management interface
- SME labeling interface and questions
- Label submission workflow and confirmation

### Data Flow Integrity:
- Configuration → API → UI consistency
- Session creation → API persistence → UI reflection  
- Trace search → linking → session display
- Label submission → API storage → verification queries

This ensures the MLflow Review App works correctly for both developers setting up labeling workflows and subject matter experts providing feedback on AI traces.