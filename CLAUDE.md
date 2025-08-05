# Databricks App Template Development Guide

## Project Memory

This is a modern full-stack application template for Databricks Apps, featuring FastAPI backend with React TypeScript frontend and modern development tooling.

## Tech Stack

**Backend:**
- Python with `uv` for package management
- FastAPI for API framework
- Databricks SDK for workspace integration
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

### 🚨 IMPORTANT: NEVER RUN THE SERVER MANUALLY 🚨

**ALWAYS use the watch script with nohup and logging:**

```bash
# Start development servers (REQUIRED COMMAND)
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &

# Or for production mode
nohup ./watch.sh --prod > /tmp/databricks-app-watch.log 2>&1 &
```

**NEVER run uvicorn or the server directly!** Always use `./watch.sh` as it:
- Configures environment variables properly
- Starts both frontend and backend correctly
- Generates TypeScript client automatically
- Handles authentication setup
- Provides proper logging and error handling

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
# ✅ CORRECT - Always source .env.local first
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks current-user me
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks apps list
source .env.local && export DATABRICKS_HOST && export DATABRICKS_TOKEN && databricks workspace list /

# ❌ WRONG - Never use databricks CLI directly
databricks current-user me
databricks apps list
databricks workspace list /
```

**Why this is required:**
- Ensures environment variables are loaded from .env.local
- Exports authentication variables to environment
- Prevents authentication failures and missing configuration

### Claude Natural Language Commands
Claude understands natural language commands for common development tasks:

**Development Lifecycle:**
- "start the devserver" → Runs `./watch.sh` in background with logging
- "kill the devserver" → Stops all background development processes
- "fix the code" → Runs `./fix.sh` to format Python and TypeScript code
- "deploy the app" → Runs `./deploy.sh` to deploy to Databricks Apps

**Development Tasks:**
- "add a new API endpoint" → Creates FastAPI routes with proper patterns
- "create a new React component" → Builds UI components using shadcn/ui
- "debug this error" → Analyzes logs and fixes issues
- "install [package]" → Adds dependencies using uv (Python) or bun (frontend)
- "generate the TypeScript client" → Regenerates API client from OpenAPI spec
- "open the UI in playwright" → Opens the frontend app in Playwright browser for testing
- "open app" → Gets app URL from `./app_status.sh` and opens it with `open {url}`

**Labeling Infrastructure Inspection:**
- "show me the labeling schemas" → Detailed view of all current schemas with types and configurations
- "show me the labeling sessions" → Comprehensive session overview with progress tracking, completion rates, assigned users, and status (mirrors UI display)

**Databricks Integration:**
- "open labeling session [name/id]" → **INTERACTIVE PROMPT**: Databricks or local app?
  - Uses `uv run python tools/open_labeling_session.py [name/id]`
  - **Databricks**: Opens production Databricks labeling session interface
  - **Local App**: Opens local development labeling session interface  
  - Can search by session name or use direct session ID
  - Queries all labeling sessions to find by name if needed
  - Example: "open labeling session test-session-1" or "open labeling session 86c89a01-7f31-4cc0-b610-f88c6ab057c2"
- "open labeling schemas" → **INTERACTIVE PROMPT**: Databricks or local app?
  - Uses `uv run python tools/open_labeling_schemas.py`
  - **Databricks**: Opens production Databricks schemas management interface
  - **Local App**: Opens local development schemas interface at http://localhost:5173/labeling-schemas
  - Beautiful CLI prompts with emojis and clear environment descriptions

**MLflow Review App Tools:**
Claude has access to specialized tools for exploring MLflow traces and review apps:

- "what traces have [xyz]" → Calls `uv run python tools/search_traces.py` with appropriate filters
- "search for traces with [condition]" → Uses search_traces tool with filter strings
- "show me traces from [timeframe/condition]" → Searches traces with date/filter parameters
- "get the review app" → Calls `uv run python tools/get_review_app.py` using config experiment_id
- "what's the review app for experiment [id]" → Gets review app by specific experiment ID
- "show me the current user" → Calls `uv run python tools/get_current_user.py`
- "get workspace info" → Calls `uv run python tools/get_workspace_info.py`
- "get trace [trace_id]" → Calls `uv run python tools/get_trace.py --trace-id [id]`
- "get trace metadata [trace_id]" → Calls `uv run python tools/get_trace_metadata.py [trace_id]` (returns trace info + span names/types only)
- "list labeling sessions" → Calls `uv run python tools/list_labeling_sessions.py` (always returns full schema details + auto-analysis)
  - **CRITICAL WORKFLOW**: Tool returns deterministic JSON output with analysis data
  - **CLAUDE MUST**: Read the JSON output and create a comprehensive, beautiful summary report including:
    - **Overall Status**: Total sessions, completion rates, engagement metrics
    - **Progress Tracking**: For each session, show completion rates, assigned users, current status (like the UI)
    - **Assessment-Oriented Analysis**: For each assessment schema, show:
      - Statistical summaries (distributions, averages, consensus levels)
      - SME response patterns and feedback themes
      - Trace content correlation analysis (what drove SME decisions)
      - Visual representations with emojis and progress bars
    - **Pattern Detection**: Identify what parts of traces correlate with specific assessments
    - **Actionable Insights**: Key findings, recommendations, sessions needing attention
  - **Returns JSON structure**:
    - `full_schemas` array with complete schema definitions
    - `analysis` object with per-session statistical analysis:
      - Completion rates and progress tracking
      - Per-schema analysis with trace correlation data
      - Assessment patterns and SME feedback analysis
      - Auto-generated insights and recommendations
  - **CRITICAL RENDERING FORMAT**: When displaying labeling sessions, always format metadata with proper line breaks:
    ```
    ## 1. **Session Name**
    
    🆔 **ID:** `session-id-here`
    
    🏃 **MLflow Run ID:** `run-id-here`
    
    👥 **Assigned Users:** user@example.com
    
    📅 **Created:** timestamp by creator
    
    🔄 **Last Updated:** timestamp by updater
    
    🔗 **Linked Traces:** X traces
    ```
    - Each metadata line must be on a separate line with blank lines between them
    - This prevents concatenation of metadata items on a single line
    - Use the exact format above to ensure proper rendering
  - **TRACE PREVIEW REQUIREMENT**: When displaying labeling sessions, MUST show:
    - Total number of linked traces in the metadata section
    - Preview of first 5 traces showing request/response snippets
    - Format: `### 📋 Trace Preview (First 5 of X traces)` followed by trace summaries
    - Each trace preview should show: trace ID, timestamp, input/output snippets (first 100 chars)
    - Use `search_traces` tool with run_id filter: `uv run python tools/search_traces.py --filter "run_id = 'session_mlflow_run_id'" --limit 5`
    - The search_traces tool/REST API endpoint should propagate MLflow SDK `search_traces()` functionality with proper run_id filtering
- "create labeling schemas" → Calls `uv run python tools/create_labeling_schemas.py` (create numeric, categorical, or text schemas)
  - Supports `--schema-type FEEDBACK|EXPECTATION` to specify schema type (default: FEEDBACK)
  - FEEDBACK schemas: for evaluating responses after they're generated
  - EXPECTATION schemas: for defining criteria or requirements upfront
- "update labeling schemas" → Calls `uv run python tools/update_labeling_schemas.py` (modify existing schemas)
- "delete labeling schemas" → Calls `uv run python tools/delete_labeling_schemas.py` (remove schemas)
- "create labeling session" → Calls `uv run python tools/create_labeling_session.py` (create sessions with users and schemas)
- "update labeling session" → Calls `uv run python tools/update_labeling_session.py` (modify existing sessions)
- "delete labeling session" → Calls `uv run python tools/delete_labeling_session.py` (remove sessions)
- "link traces to session" → Calls `uv run python tools/link_traces_to_session.py`
- "get trace URLs" → Calls `uv run python tools/get_trace_urls.py [review_app_id]` (gets URLs for traces in labeling sessions)
- "get experiment URL" → Calls `uv run python tools/get_experiment_url.py` (prints MLflow experiment URL)
- "open the traces tab in databricks" → Uses experiment URL with `open` command to launch browser
- "get databricks labeling session link [session_id]" → Calls `uv run python tools/databricks_get_labeling_session_link.py [experiment_id] [session_id]` (generates Databricks labeling session URL)
- "get databricks labeling schemas link" → Calls `uv run python tools/databricks_get_labeling_schemas_link.py [experiment_id]` (generates Databricks labeling schemas URL)
- "get app labeling session link [session_id]" → Calls `uv run python tools/app_get_labeling_session_link.py [review_app_id] [session_id]` (generates local app labeling session URL)
- "get app labeling schemas link" → Calls `uv run python tools/app_get_labeling_schemas_link.py` (generates local app labeling schemas URL)
- "analyze labeling results [session_name]" → Calls `uv run python tools/analyze_labeling_results.py [review_app_id] --session-name [name]`
  - Comprehensive statistical analysis of SME labeling results
  - **Categorical schemas**: Count/percentage distributions, consensus analysis  
  - **Numeric schemas**: Mean, median, std deviation, range, distribution visualization
  - **Text schemas**: Response length analysis, word frequency, sample responses
  - **Key insights**: Auto-generated findings about agreement, outliers, schema effectiveness
  - Supports filtering by session name, ID, or criteria (e.g., state=COMPLETED)
  - Output formats: beautiful CLI text (default) or JSON for programmatic use
- "open labeling session [name/id]" → Calls `uv run python tools/open_labeling_session.py [name/id]` (interactive prompt for Databricks vs local app)
- "open labeling schemas" → Calls `uv run python tools/open_labeling_schemas.py` (interactive prompt for Databricks vs local app)
- "log feedback on trace [trace_id]" → Calls `uv run python tools/log_feedback.py [trace_id] [feedback_key] [feedback_value] [--comment "comment"]` (log feedback/evaluation on traces)
  - Supports multiple data types: string, int, float, bool, list
  - Used for evaluating traces after they've been generated
  - Example: `uv run python tools/log_feedback.py tr-123 quality 4 --comment "Good response"`
- "log expectation on trace [trace_id]" → Calls `uv run python tools/log_expectation.py [trace_id] [expectation_key] [expectation_value] [--comment "comment"]` (log expectations/requirements on traces)
  - Supports multiple data types: string, int, float, bool, list, dict
  - Used for defining criteria or requirements upfront
  - Example: `uv run python tools/log_expectation.py tr-123 response_format "JSON" --comment "Should return structured data"`

**Unified CLI Tool:**
The project includes a unified CLI tool that provides discovery and centralized access to all individual tools:

- **`./mlflow-cli list`** - List all available tools grouped by category
- **`./mlflow-cli list [category]`** - List tools in specific category (user, traces, labeling, etc.)
- **`./mlflow-cli categories`** - Show all available tool categories
- **`./mlflow-cli search [query]`** - Search tools by name or description
- **`./mlflow-cli help [tool]`** - Show detailed help for a specific tool
- **`./mlflow-cli run [tool] [args...]`** - Run any tool with arguments
- **`uv run python cli.py`** - Direct access to unified CLI (equivalent to ./mlflow-cli)

Examples:
```bash
./mlflow-cli list traces                    # List trace-related tools
./mlflow-cli search user                    # Find user-related tools
./mlflow-cli help search_traces             # Get help for search_traces
./mlflow-cli run search_traces --limit 5    # Run search_traces with args
```

**Tool Behaviors:**
- All tools use the centralized config experiment_id by default (from config.yaml)
- Tools can accept explicit parameters to override defaults
- Search filters support MLflow trace syntax (e.g., "tags.user = 'john'" or "metadata.status = 'completed'")
- **CRITICAL: ALWAYS run `./mlflow-cli help [tool]` or `uv run python tools/[tool].py --help` before using any tool to see current parameter options and examples**

**Search Traces Advanced Features:**
- Supports SQL-like filtering: `status = 'OK' AND execution_time_ms > 1000`
- Tag filtering: `tags.model_name = 'gpt-4'` or `tag.user = 'alice'`
- Metadata filtering: `metadata.version = '2.1'`
- Status filtering: `status IN ('OK', 'ERROR')`
- Time-based: `timestamp_ms > 1735689600000` (Unix timestamp in ms)
- Ordering: `--order-by "timestamp_ms DESC"` or `--order-by "execution_time_ms ASC"`
- Performance analysis: Find slow traces with `execution_time_ms > 5000`
- Error investigation: `status = 'ERROR'` with recent first ordering

**Slash Commands:**
Interactive commands for managing MLflow Review App components:

- **`/label-schemas`** - Manage labeling schemas
  - `/label-schemas` → List all schemas with beautiful CLI formatting
  - `/label-schemas add [description]` → Add new schema with natural language guidance
  - `/label-schemas modify [schema_name] [changes]` → Update existing schema with confirmation
  - `/label-schemas delete [schema_name]` → Delete schema with confirmation
  - **Implementation**: Uses `.claude/commands/label-schemas.md` which orchestrates tools in `tools/`

- **`/labeling-sessions`** - Manage labeling sessions  
  - `/labeling-sessions` → List all sessions with status, users, traces, links, and **auto-analysis**
  - `/labeling-sessions add [description]` → Create new session with natural language guidance
  - `/labeling-sessions modify [session_name] [changes]` → Update existing session with confirmation
  - `/labeling-sessions delete [session_name]` → Delete session with confirmation
  - `/labeling-sessions link [session_name] [trace_criteria]` → Link traces to session
  - `/labeling-sessions analyze [session_name]` → **NEW**: Generate statistical analysis of SME results
  - **Implementation**: Uses `.claude/commands/labeling-sessions.md` which orchestrates tools in `tools/`

Both slash commands provide:
- Beautiful CLI rendering with emojis and structured output
- Natural language parsing and guidance
- Dry-run previews before making changes
- Explicit confirmation prompts for destructive actions
- Integration with existing tools that use shared utilities

### Implementation Validation Workflow
**During implementation, ALWAYS:**
1. **Start development server first**: `nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &`
2. **Open app with Playwright** to see current state before changes
3. **After each implementation step:**
   - Check logs: `tail -f /tmp/databricks-app-watch.log`
   - Use Playwright to verify UI changes are working
   - Take snapshots to confirm features render correctly
   - Test user interactions and API calls
4. **🚨 CRITICAL: FastAPI Endpoint Verification**
   - **IMPORTANT: After adding ANY new FastAPI endpoint, MUST curl the endpoint to verify it works**
   - **NEVER move on to the next step until the endpoint is verified with curl**
   - **Example verification commands:**
     ```bash
     # Test GET endpoint
     curl -s http://localhost:8000/api/new-endpoint | jq
     
     # Test POST endpoint
     curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' http://localhost:8000/api/new-endpoint | jq
     ```
   - **Show the curl response to confirm the endpoint works correctly**
   - **If the endpoint fails, debug and fix it before proceeding**
5. **Install Playwright if needed**: `claude mcp add playwright npx '@playwright/mcp@latest'`
6. **Iterative validation**: Test each feature before moving to next step

**This ensures every implementation step is validated and working before proceeding.**

### Development Server
- **ALWAYS** run `./watch.sh` with nohup in background and log to file for debugging
- Watch script automatically runs in background and logs to `/tmp/databricks-app-watch.log`
- Frontend runs on http://localhost:5173
- Backend runs on http://localhost:8000
- API docs available at http://localhost:8000/docs
- Supports hot reloading for both frontend and backend
- Automatically generates TypeScript client from FastAPI OpenAPI spec
- **Check logs**: `tail -f /tmp/databricks-app-watch.log`
- **Stop processes**: `pkill -f "watch.sh"` or check PID file

### Code Quality
- Use `./fix.sh` for code formatting before commits
- Python: ruff for formatting and linting, ty for type checking
- TypeScript: prettier for formatting, ESLint for linting
- Type checking with TypeScript and ty (Python)

### API Development
- FastAPI automatically generates OpenAPI spec
- TypeScript client is auto-generated from OpenAPI spec
- Test endpoints with curl or FastAPI docs
- Check server logs after requests
- Verify response includes expected fields
- **Type Safety**: Use proper Pydantic models instead of Dict[str, Any]
- **Error Handling**: Custom exceptions are automatically converted to JSON responses with toast notifications
- **React Query**: All API calls should use React Query hooks (useQuery for GET, useMutation for POST/PUT/DELETE)

### Databricks API Integration
- **ALWAYS** reference `docs/databricks_apis/` documentation when implementing Databricks features
- Use `docs/databricks_apis/databricks_sdk.md` for workspace, cluster, and SQL operations
- Use `docs/databricks_apis/mlflow_genai.md` for AI agent and LLM functionality
- Use `docs/databricks_apis/model_serving.md` for model serving endpoints and inference
- Use `docs/databricks_apis/workspace_apis.md` for file operations and directory management
- Follow the documented patterns and examples for proper API usage
- Check official documentation links in each API guide for latest updates

### Frontend Development
- Use shadcn/ui components for consistent UI
- Follow React Query patterns for API calls
- Use TypeScript strictly - no `any` types
- Import from auto-generated client: `import { apiClient } from '@/fastapi_client'`
- Client uses shadcn/ui components with proper TypeScript configuration
- shadcn components must be added with: npx shadcn@latest add <component-name>

### Testing Methodology
- Test API endpoints using FastAPI docs interface
- Use browser dev tools for frontend debugging
- Check network tab for API request/response inspection
- Verify console for any JavaScript errors

### Deployment
- Use `./deploy.sh` for Databricks Apps deployment
- Automatically builds frontend and generates requirements.txt
- Configures app.yaml with environment variables
- Verifies deployment through Databricks CLI
- **IMPORTANT**: After deployment, monitor `/logz` endpoint of your Databricks app to check for installation issues
- App logs are available at: `https://<app-url>/logz` (visit in browser - requires OAuth authentication)

### Environment Configuration
- Use `.env.local` for local development configuration
- Set environment variables and Databricks credentials
- Never commit `.env.local` to version control
- Use `./setup.sh` to create and update environment configuration

### MLflow Configuration
- **Primary config file**: `config.yaml` contains only the MLflow experiment_id
- **Configuration format**: When updating experiment_id, always use this exact format:
  ```yaml
  # MLflow Review App Configuration
  mlflow:
    experiment_id: 'your_experiment_id_here'
  ```
- **Tools for config management**:
  - `uv run python tools/get_experiment_info.py [id_or_name]` - Get experiment details
  - `uv run python tools/update_config_experiment.py [experiment_id]` - Update config.yaml
- **Note**: Experiment ID should always be a string in quotes, not a number

### Experiment Analysis and Summarization
When users ask to "summarize an experiment", use this comprehensive analysis approach:

**Note**: Databricks experiment links always follow this format:
```
https://[workspace-url]/ml/experiments/[experiment_id]/traces?o=[workspace_id]
```
Example: `https://eng-ml-inference-team-us-west-2.cloud.databricks.com/ml/experiments/2178582188830602/traces?o=5722066275360235`

To extract the experiment_id from a Databricks URL, look for the number after `/ml/experiments/`.

1. **Get experiment information**:
   ```bash
   uv run python tools/get_experiment_info.py [experiment_id_or_name]
   ```

2. **Analyze broad trace patterns** (~50 traces):
   ```bash
   uv run python tools/analyze_trace_patterns.py --experiment-id [experiment_id] --limit 50
   ```

3. **Examine detailed traces with spans** (5 traces):
   ```bash
   uv run python tools/search_traces.py --limit 5 --include-spans --order-by "timestamp_ms DESC" --experiment-id [experiment_id]
   ```

4. **Generate comprehensive analysis report** including:
   - **Experiment Overview**: Name, ID, URL, trace count
   - **Agent Type**: Multi-agent, single-agent, tool-calling patterns
   - **Key Capabilities**: What the agent can do (catalog management, SQL operations, etc.)
   - **Agent Architecture**: Main components (agent, executor, LLM integration)
   - **Tool Usage Patterns**: Number of tools, calling patterns (sequential/parallel), context-awareness
   - **Request/Response Flow**: How the agent processes user inputs and generates outputs
   - **Specific Use Cases**: Examples of what the agent handles based on actual trace data
   - **Existing Labeling Infrastructure**: Current schemas and active labeling sessions

**Example Analysis Output Format**:
```
🧪 Experiment: [Experiment Name]
🆔 ID: [experiment_id]  
🔗 URL: [workspace_url]/#/experiments/[experiment_id]
📈 Traces: [count] traces available

Agent Pattern Analysis:
====================
Agent Type: [Multi-agent SQL/Analytics Assistant with X+ specialized tools]

Key Capabilities:
- [Capability 1]: [Description]
- [Capability 2]: [Description]
- [Capability N]: [Description]

Agent Architecture:
1. [Main Agent]: [Description and span type]
2. [Execution Chain]: [How orchestration works]
3. [LLM Integration]: [Model used for reasoning]
4. [Tool Selection]: [Calling pattern description]

Tool Usage Pattern:
- [X different tools] detected across traces
- [Sequential/Parallel execution] pattern
- [Context-aware] tool selection based on user requests
- [Multi-step workflows] that build on previous tool outputs

This analysis helps you understand exactly what your agent does and how to design 
appropriate labeling schemas for evaluation.
```

This approach provides deep insights into agent behavior and helps users understand their AI systems for better evaluation design.

**Experiment Summary Storage**:
- **Location**: All experiment summaries are automatically saved to `experiments/[experiment_id]_summary.md`
- **Format**: Complete markdown files with comprehensive analysis, agent patterns, and evaluation recommendations
- **Usage**: These summaries serve as references for designing labeling schemas and creating targeted labeling sessions
- **Benefits**: Provides context-aware schema suggestions based on specific agent capabilities and use cases

**Example**: When users ask to summarize experiment `2178582188830602`, the analysis is saved to `experiments/2178582188830602_summary.md` and can be referenced later for:
- Suggesting appropriate labeling schemas for multi-tool agents
- Creating labeling sessions focused on tool selection accuracy
- Designing evaluation criteria for complex analytical workflows
- Understanding existing evaluation infrastructure (current schemas and sessions)

### Debugging Tips
- Verify environment variables are set correctly
- Use FastAPI docs for API testing: http://localhost:8000/docs
- Check browser console for frontend errors
- Use React Query DevTools for API state inspection
- **Check watch logs**: `tail -f /tmp/databricks-app-watch.log` for all development server output
- **Check process status**: `ps aux | grep databricks-app` or check PID file at `/tmp/databricks-app-watch.pid`
- **Force stop**: `kill $(cat /tmp/databricks-app-watch.pid)` or `pkill -f watch.sh`

### Key Files
- `server/app.py` - FastAPI application entry point
- `server/routers/` - API endpoint routers
- `client/src/App.tsx` - React application entry point
- `client/src/pages/` - React page components
- `client/src/session-renderer/` - Custom session renderer system
- `scripts/make_fastapi_client.py` - TypeScript client generator
- `pyproject.toml` - Python dependencies and project configuration
- `client/package.json` - Frontend dependencies and scripts
- `claude_scripts/` - Test scripts created by Claude for testing functionality

### API Documentation
- `docs/databricks_apis/` - Comprehensive API documentation for Databricks integrations
- `docs/databricks_apis/databricks_sdk.md` - Databricks SDK usage patterns
- `docs/databricks_apis/mlflow_genai.md` - MLflow GenAI for AI agents
- `docs/databricks_apis/model_serving.md` - Model serving endpoints and inference
- `docs/databricks_apis/workspace_apis.md` - Workspace file operations

### Documentation Files
- `docs/product.md` - Product requirements document (created during /dba workflow)
- `docs/design.md` - Technical design document (created during /dba workflow)
- These files are generated through iterative collaboration with the user during the /dba command

### Common Issues
- If TypeScript client is not found, run the client generation script manually
- If hot reload not working, restart `./watch.sh`
- If dependencies missing, run `./setup.sh` to reinstall

Remember: This is a development template focused on rapid iteration and modern tooling.

## Session Renderer System

The MLflow Review App includes a comprehensive session renderer system that allows users to customize how traces and labeling schemas are displayed in the UI.

### Architecture Overview

- **Location**: `client/src/session-renderer/`
- **Registry System**: Dynamic renderer management with type safety
- **MLflow Integration**: Renderer selection stored in MLflow run tags
- **Claude Code Friendly**: AI can help create and modify custom renderers

### Key Components

- **`session-renderer/renderers/index.ts`** - Registry system managing all available renderers
- **`session-renderer/renderers/DefaultItemRenderer.tsx`** - Standard conversation view (preserves existing functionality)
- **`session-renderer/renderers/CompactTimelineRenderer.tsx`** - Timeline-based view with quick stats
- **`components/RendererSelector.tsx`** - UI for choosing and applying renderers in dev mode
- **`types/renderers.ts`** - TypeScript interfaces for type-safe renderer development

### How It Works

1. **Development Mode**: Use the Renderer Selector card to choose how traces are displayed
2. **Persistence**: Renderer choice is saved to MLflow run tags (`mlflow.customRenderer`)
3. **SME Experience**: Chosen renderer loads automatically in SME labeling mode
4. **Custom Creation**: Users can create React components with full control over trace display and labeling schema placement

### Available Renderers

- **Default Renderer**: Standard conversation view with full labeling forms
- **Compact Timeline**: Timeline-based view with quick stats and streamlined interface

### Creating Custom Renderers

Users can create custom renderers by:
1. Creating a React component that accepts `ItemRendererProps`
2. Registering it in the renderer registry
3. Selecting it via the dev mode interface
4. Getting Claude Code assistance for component creation and modification

### Natural Language Commands

- "create a renderer focused on tool usage analysis" → Claude creates specialized tool-focused renderer
- "add a compact card-based renderer for mobile review" → Claude designs mobile-optimized interface
- "build a renderer that highlights errors and performance issues" → Claude creates error-focused renderer

The system provides complete control over the trace review experience while maintaining type safety and ease of use.

## MLflow Review App Architecture

### Core Concepts and Component Relationships

The MLflow Review App template integrates several key components that work together to enable AI/ML model evaluation workflows:

#### 1. MLflow Experiments and Traces
- **MLflow Experiments**: Container for ML runs and traces
- **Traces**: Individual AI agent interactions or model inferences that need human review
- **Trace Components**:
  - `trace_id`: Unique identifier for each trace
  - `trace_info`: Metadata including timestamps, execution duration, state
  - `trace_data`: Actual input/output data and spans
  - `experiment_id`: Links trace to its parent experiment

#### 2. Review Apps
- **Purpose**: Define the evaluation framework for an experiment
- **Key Properties**:
  - `review_app_id`: Unique identifier
  - `experiment_id`: Links to MLflow experiment containing traces
  - `labeling_schemas`: Define what aspects to evaluate (e.g., quality ratings, feedback categories)
- **Relationship**: One Review App per Experiment (1:1)

#### 3. Labeling Sessions
- **Purpose**: Organize batches of traces for human review
- **Key Properties**:
  - `labeling_session_id`: Unique identifier
  - `mlflow_run_id`: **CRITICAL** - This is an MLflow run that acts as a container for linked traces
  - `assigned_users`: Who should review the traces
  - `labeling_schemas`: Subset of review app schemas to use
- **Relationship**: Many Labeling Sessions per Review App (1:N)

#### 4. Trace Linking Methodology (NOT Copying!)
- **Important**: We use trace LINKING, not trace copying
- **How it works**:
  1. Labeling session has an `mlflow_run_id`
  2. Use `/api/mlflow/traces/link-to-run` to link existing traces to this run
  3. Traces remain in their original location but are now associated with the labeling session
  4. Multiple labeling sessions can link to the same trace (many-to-one relationship)
- **Benefits**:
  - Non-destructive: Original traces are preserved
  - Efficient: No data duplication
  - Flexible: Same trace can be in multiple labeling sessions

#### 5. Labeling Items
- **Purpose**: Track individual trace review status within a session
- **Note**: Items are typically created automatically when traces are linked
- **Properties**:
  - `item_id`: Unique identifier
  - `source.trace_id`: Reference to the linked trace
  - `state`: PENDING, IN_PROGRESS, COMPLETED, SKIPPED
  - Labels/feedback from reviewers

### Data Flow Example

```
1. MLflow Experiment (ID: 2178582188830602)
   └── Contains many traces from AI agent interactions

2. Create Review App
   └── Defines evaluation criteria (quality ratings, helpfulness, etc.)

3. Create Labeling Session
   └── Gets an mlflow_run_id (e.g., 27c42c9d1bff4184acf02c58fbc2b1f5)

4. Search for Traces to Review
   └── Use search_traces endpoint with filters

5. Link Traces to Labeling Session
   └── POST /api/mlflow/traces/link-to-run
       {
         "run_id": "27c42c9d1bff4184acf02c58fbc2b1f5",
         "trace_ids": ["tr-6524c1867f1317f082594bc26f14dbe7"]
       }

6. Verify Traces are Linked
   └── Search traces with run_id filter returns linked traces
```

### API Endpoint Categories

1. **MLflow Proxies** (`/api/mlflow/*`): Direct access to MLflow APIs
   - Experiments, runs, traces operations
   - Special: `search-traces` uses SDK (no direct API)

2. **Review Apps** (`/api/review-apps/*`): Managed evaluation framework
   - Standard API path: `/api/2.0/managed-evals/`
   - NOT ajax-api (never use ajax-api endpoints)

3. **Labeling Sessions** (`/api/review-apps/{id}/labeling-sessions/*`)
   - CRUD operations for session management
   - Each session is backed by an MLflow run

4. **Labeling Items** (`/api/review-apps/{id}/labeling-sessions/{id}/items/*`)
   - Read and update only (no direct create/delete)
   - Items appear when traces are linked to the session

### Important Implementation Notes

- **Authentication**: All APIs use Bearer token from DATABRICKS_TOKEN env var
- **Empty Responses**: Some Databricks APIs return empty responses - normalize these in endpoints
- **URL Patterns**: Use standard `/api/2.0/` paths, never `/ajax-api/`
- **Trace Linking**: Always use link-to-run methodology, never copy traces
- **Search Traces**: Implemented via MLflow SDK as there's no direct API endpoint
- **User Management**: Use MLflow SDK (`mlflow.genai.labeling`) for adding/removing users from labeling sessions - it automatically handles experiment permissions

### Labeling Schema Visual Representations

When displaying labeling schemas to users, always show visual representations that match how they appear in the Databricks labeling interface:

#### Categorical Schema (True/False)
```
┌─────────────────────────────────────────────────────────────────┐
│ Feedback                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ● Correctness                                                ▲ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Is the response correct?                                        │
│                                                                 │
│ ○ True                                                          │
│                                                                 │
│ ○ False                                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Categorical Schema (Multiple Options)
```
┌─────────────────────────────────────────────────────────────────┐
│ Feedback                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ● Helpfulness                                               ▲ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Was the response helpful?                                       │
│                                                                 │
│ ○ Very Helpful                                                  │
│                                                                 │
│ ○ Somewhat Helpful                                              │
│                                                                 │
│ ○ Not Helpful                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Numeric Rating Schema
```
┌─────────────────────────────────────────────────────────────────┐
│ Feedback                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ● Response Quality                                           ▲ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Rate the quality of the AI response                             │
│                                                                 │
│ [     5.0     ] ◄─────────────────────► Min: 1.0, Max: 5.0    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Text Feedback Schema
```
┌─────────────────────────────────────────────────────────────────┐
│ Feedback                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ● General Feedback                                           ▲ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Provide detailed feedback about the response                    │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ [Text input area - up to 500 characters]                   │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Schema WITH Comments Enabled
```
┌─────────────────────────────────────────────────────────────────┐
│ Feedback                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ● Helpfulness Assessment                                     ▲ │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Rate the helpfulness and provide reasoning                      │
│                                                                 │
│ ○ Very Helpful                                                  │
│                                                                 │
│ ○ Somewhat Helpful                                              │
│                                                                 │
│ ○ Not Helpful                                                   │
│                                                                 │
│ Comments (Optional):                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │ [Rationale/reasoning text area]                             │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Visual Elements:**
- **Header:** Shows "Feedback" section
- **Title:** Schema name with expand/collapse arrow (▲)
- **Instruction:** Clear guidance text
- **Input Controls:** Radio buttons (○), sliders, text areas
- **Comments:** Optional text area when `enable_comment: true`
- **Constraints:** Min/max values for numeric schemas

**Schema Types Summary:**
- **Categorical:** Radio button selection, supports comments
- **Numeric:** Slider/input with min/max range, supports comments  
- **Text:** Text area input, inherently supports detailed feedback

Always use these visual representations when showing schemas to help users understand exactly how they will appear in the Databricks labeling interface.