# 🎯 MLflow Review App - Custom Evaluation Framework

[![Databricks Apps](https://img.shields.io/badge/Databricks-Apps-orange)](https://docs.databricks.com/en/dev-tools/databricks-apps/)
[![MLflow](https://img.shields.io/badge/MLflow-Integration-red)](https://mlflow.org/docs/latest/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)](https://www.typescriptlang.org/)
[![Claude](https://img.shields.io/badge/Claude_Code-Ready-purple)](https://claude.ai/code)

This template allows you to build custom review apps on Databricks Apps for collecting labels from Subject Matter Experts. Customize how MLflow traces are displayed—show specific spans, filter certain data, or present information differently than the standard Databricks review app. Create tailored labeling interfaces for your domain, collect targeted feedback for model improvement, and leverage integrated AI analysis for experiment optimization and result summarization.

## 🎬 Demo Video

Watch a **complete walkthrough** of building a custom MLflow Review App using Claude Code's `/review-app` command:

📹 **[Watch the Full Tutorial](https://youtu.be/xdvodY9-VQQ)** - See how to customize, deploy, and use the review app from start to finish

[![MLflow Review App Demo](https://img.shields.io/badge/Watch-Demo_Video-red?style=for-the-badge&logo=youtube)](https://youtu.be/xdvodY9-VQQ)

## 🚀 Quick Start

The setup script automatically handles all dependencies - just run it!

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
// AnalyticsRenderer.tsx
import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ItemRendererProps } from "@/types/renderers";
import { LabelSchemaForm } from "./schemas/LabelSchemaForm";
import { BarChart3, AlertCircle, CheckCircle } from "lucide-react";

export function AnalyticsRenderer({
  item,
  traceData,
  reviewApp,
  session,
  currentIndex,
  totalItems,
  assessments,
  onUpdateItem,
  onNavigateToIndex,
  isSubmitting,
  schemaAssessments,
}: ItemRendererProps) {
  // Extract analytics-relevant data from trace spans
  const spans = traceData?.spans || [];
  const querySpans = spans.filter(s => s.name?.includes("query"));
  const totalDuration = spans[0]?.end_time - spans[0]?.start_time || 0;
  
  // Separate feedback and expectation schemas
  const feedbackSchemas = schemaAssessments?.feedback || [];
  const expectationSchemas = schemaAssessments?.expectations || [];
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Query Analytics */}
      <div className="lg:col-span-2 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Query Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Duration</p>
                  <p className="text-2xl font-bold">{totalDuration.toFixed(2)}ms</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Query Count</p>
                  <p className="text-2xl font-bold">{querySpans.length}</p>
                </div>
              </div>
              
              {/* Show individual query details */}
              {querySpans.map((span, idx) => (
                <div key={idx} className="border-l-2 border-blue-500 pl-4">
                  <p className="font-medium">{span.name}</p>
                  <pre className="text-xs text-muted-foreground mt-1">
                    {JSON.stringify(span.inputs, null, 2).slice(0, 200)}...
                  </pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Right: Evaluation Forms */}
      <div className="space-y-6">
        {feedbackSchemas.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3">Performance Assessment</h3>
            <LabelSchemaForm
              schemas={feedbackSchemas.map(item => item.schema)}
              assessments={new Map(
                feedbackSchemas
                  .filter(item => item.assessment)
                  .map(item => [item.schema.name, item.assessment!])
              )}
              traceId={item.source?.trace_id || ""}
              readOnly={false}
              reviewAppId={reviewApp.review_app_id}
              sessionId={session.labeling_session_id}
            />
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => onUpdateItem(item.item_id, { state: "SKIPPED" })}
          >
            Skip
          </Button>
          <Button
            onClick={() => onUpdateItem(item.item_id, { state: "COMPLETED" })}
            disabled={isSubmitting || assessments.size === 0}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Submit
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Register Your Renderer**

Add to `client/src/components/session-renderer/renderers/index.ts`:

```typescript
import { AnalyticsRenderer } from "./AnalyticsRenderer";

// In the constructor, add:
this.registerRenderer({
  name: "analytics",                    // Internal name (used in MLflow tag)
  displayName: "Analytics View",        // Display name in UI
  description: "Performance metrics and query analysis view",
  component: AnalyticsRenderer,         // Your component
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