# 🎯 MLflow Review App - Custom Evaluation Framework

[![Databricks Apps](https://img.shields.io/badge/Databricks-Apps-orange)](https://docs.databricks.com/en/dev-tools/databricks-apps/)
[![MLflow](https://img.shields.io/badge/MLflow-Integration-red)](https://mlflow.org/docs/latest/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)](https://www.typescriptlang.org/)
[![Claude](https://img.shields.io/badge/Claude_Code-Ready-purple)](https://claude.ai/code)

Build custom [review apps](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/concepts/review-app) on Databricks Apps with tailored UIs for your subject matter experts to evaluate AI agent traces.

## 🚀 Quick Start

### Prerequisites

The setup script checks for required tools and handles installation:
- **uv** - Python package manager (prompts to install if missing)
- **Databricks CLI** - Workspace integration (auto-installs via brew if missing)
- **bun** - JavaScript package manager (optional, uses npm as fallback)

### Choose Your Path

#### 🤖 AI-Powered Setup (Claude Code)

```
/review-app
```

Claude handles everything automatically:
- ✅ Environment setup
- ✅ Experiment analysis
- ✅ Custom schema creation
- ✅ Session configuration
- ✅ Deployment

#### 🛠️ Manual Setup

```bash
./setup.sh   # Interactive setup wizard - handles all configuration
./watch.sh   # Start dev servers (frontend:5173, backend:8000)
```

## 🎨 Customization Guide

### Custom Renderers - Customize What SMEs See

The renderer system lets you completely customize how subject matter experts view and evaluate traces. Renderers are stored as MLflow tags (`mlflow.evaluation.renderer`) on labeling sessions and can be changed dynamically.

#### Creating a Custom Renderer

**Step 1: Create Your Renderer Component**

Create a new file in `client/src/components/session-renderer/renderers/`:

```typescript
// YourCustomRenderer.tsx
import { ItemRendererProps } from "@/types/renderers";

export function YourCustomRenderer({
  item,              // Current labeling item with state
  traceData,         // Complete MLflow trace with spans
  reviewApp,         // Review app configuration
  assessments,       // Current assessment values (Map)
  onUpdateItem,      // Update function with auto-save
  currentIndex,      // Current position (0-based)
  totalItems,        // Total items in session
}: ItemRendererProps) {
  
  // Access trace spans for custom visualization
  const spans = traceData?.spans || [];
  const toolCalls = spans.filter(s => s.type === "TOOL");
  
  return (
    <div className="space-y-4">
      {/* Your custom trace visualization */}
      <div>
        {toolCalls.map(tool => (
          <div key={tool.name}>
            Tool: {tool.name}
            Input: {JSON.stringify(tool.inputs)}
          </div>
        ))}
      </div>
      
      {/* Custom evaluation interface */}
      {reviewApp.labeling_schemas.map(schema => (
        <div key={schema.name}>
          {/* Render your custom evaluation UI */}
        </div>
      ))}
      
      {/* Submit/Skip actions */}
      <button onClick={() => onUpdateItem(item.item_id, { state: "COMPLETED" })}>
        Submit
      </button>
    </div>
  );
}
```

**Step 2: Register Your Renderer**

Add to `client/src/components/session-renderer/renderers/index.ts`:

```typescript
import { YourCustomRenderer } from "./YourCustomRenderer";

// In the constructor, add:
this.registerRenderer({
  name: "your-custom-view",           // Internal name (used in MLflow tag)
  displayName: "Your Custom View",    // Display name in UI
  description: "Description of what makes this view special",
  component: YourCustomRenderer,      // Your component
});
```

**Step 3: Use Your Renderer**

Go to the UI and choose from the dropdown to select your custom renderer.

#### Renderer API Reference

Your renderer receives these props:

```typescript
interface ItemRendererProps {
  // Core Data
  item: LabelingItem;           // Current item (id, state, comment)
  traceData: TraceData;         // Full trace with spans
  reviewApp: ReviewApp;         // Review app with schemas
  session: LabelingSession;     // Current session details
  
  // Navigation
  currentIndex: number;         // Current position (0-based)
  totalItems: number;          // Total items count
  onNavigateToIndex: (i) => void;  // Jump to item
  
  // Assessment Management
  assessments: Map<string, Assessment>;  // Current values
  onUpdateItem: async (          // Auto-save function
    itemId: string,
    updates: { 
      state?: "COMPLETED" | "SKIPPED";
      assessments?: Map<string, Assessment>;
      comment?: string;
    }
  ) => void;
  
  // UI State
  isLoading?: boolean;         // Data loading
  isSubmitting?: boolean;      // Save in progress
}
```

#### Built-in Renderers

- **Default Renderer**: Full conversation view with detailed labeling forms
- **Tool Renderer**: Enhanced view showing tool execution details

## 🚀 Deployment

```bash
./deploy.sh          # Deploy to existing Databricks App
./deploy.sh --create # Create new app and deploy
./deploy.sh --verbose # Deploy with detailed logging
```

### Post-Deployment Verification

Always verify deployment success:
```bash
# Check app status
uv run python app_status.py --format json

# Monitor logs (replace with your app URL)
uv run python dba_logz.py https://your-app.databricksapps.com --search "INFO"

# Test health endpoint
uv run python dba_client.py https://your-app.databricksapps.com /health
```

## 🧰 MLflow CLI

The MLflow CLI provides 38 tools organized into categories for complete review app management:

**Key Categories:**
- **LABELING** - Create/manage schemas and sessions
- **TRACES** - Search and link MLflow traces  
- **ANALYTICS** - AI-powered analysis and reporting
- **MLFLOW** - Experiment and permissions management

**Essential Commands:**
```bash
./mlflow-cli list                    # List all 38 tools
./mlflow-cli list labeling          # List labeling tools
./mlflow-cli search <query>         # Search for specific tools
./mlflow-cli help <tool>            # Get detailed help
./mlflow-cli run <tool> [args]      # Execute a tool
```

**Common Operations:**
```bash
# Create evaluation schemas
./mlflow-cli run create_labeling_schemas --preset quality-helpfulness

# Set up review session
./mlflow-cli run create_labeling_session --name "Review Session"

# Link traces to session
./mlflow-cli run link_traces_to_session --session-name "Review Session" --limit 100

# Analyze results
./mlflow-cli run ai_analyze_session --session-name "Review Session"
```

## 📁 Project Structure

```
├── server/                    # FastAPI backend
│   ├── routers/              # API endpoints
│   ├── models/               # Data models
│   └── utils/                # Utilities
│
├── client/                   # React frontend
│   └── src/
│       ├── pages/           # Main UI pages
│       ├── components/      # Reusable components
│       └── session-renderer/ # Custom trace renderers
│
├── tools/                    # MLflow CLI tools
├── scripts/                  # Python build scripts
├── setup.sh                  # Environment setup
├── watch.sh                  # Start dev servers
├── deploy.sh                 # Deploy to Databricks
└── mlflow-cli                # CLI wrapper
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Dev server issues | `pkill -f watch.sh && ./watch.sh` |
| Auth errors | Re-run `./setup.sh` |
| Missing TypeScript client | `uv run python scripts/make_fastapi_client.py` |
| Deployment failures | Check logs with `dba_logz.py` |
| API 404 errors | Verify router registration in `server/app.py` |

## 📖 Resources

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Claude Code](https://claude.ai/code) - For AI-powered development

---

Ready to evaluate your AI agents? Start with `./setup.sh` or `/review-app` in Claude Code.