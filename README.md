# 🎯 Custom MLflow Review App

```
╭─────────────────────────────────────────────────────────────────────────────╮
│                                                                             │
│   🎯 MLflow Review App - Transform Traces into Evaluation Platform         │
│                                                                             │
│   Production-ready human feedback system for MLflow AI agents              │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯
```

![Databricks Apps](https://img.shields.io/badge/Databricks-Apps-orange)
![MLflow](https://img.shields.io/badge/MLflow-Integration-red)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![React](https://img.shields.io/badge/React-18+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)
![Claude](https://img.shields.io/badge/Claude_Code-Ready-purple)

## 🚀 What You'll Get

This **production-ready review app** provides:

```
┌─ 🎯 Trace Evaluation ─────────────────────────┐  ┌─ 📊 Custom Schemas ──────────────────────────┐
│ • Review AI agent interactions               │  │ • Ratings, categories, text feedback        │
│ • Rate response quality and accuracy         │  │ • Visual schema builder                      │
│ • Track completion across reviewers          │  │ • Agent-specific evaluation criteria         │
└───────────────────────────────────────────────┘  └──────────────────────────────────────────────┘

┌─ 👥 SME Workflows ────────────────────────────┐  ┌─ 📈 Analytics Dashboard ─────────────────────┐
│ • Assign experts to review sessions          │  │ • Feedback pattern analysis                 │
│ • Progress tracking and notifications        │  │ • Inter-rater agreement metrics             │
│ • Custom thank you messages                  │  │ • Export results for further analysis       │
└───────────────────────────────────────────────┘  └──────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install required tools
curl -LsSf https://astral.sh/uv/install.sh | sh  # Python package manager
curl -fsSL https://bun.sh/install | bash          # JavaScript package manager
brew install databricks                           # Databricks CLI
```

### Choose Your Path

<table>
<tr>
<td width="50%">

### 🤖 With Claude Code

**Recommended for AI-powered customization**

1. **Open in Claude Code**
   ```bash
   git clone <your-repo>
   cd custom-mlflow-review-app
   # Open in Claude Code
   ```

2. **Run the review-app command**
   ```
   /review-app analyze my SQL agent
   ```

3. **Claude will:**
   - ✅ Run setup.sh automatically
   - ✅ Start development servers
   - ✅ Analyze your experiment
   - ✅ Create custom schemas
   - ✅ Set up labeling sessions
   - ✅ Deploy when ready

**Benefits:**
- AI analyzes your agent patterns
- Suggests optimal evaluation criteria
- Creates everything automatically
- Interactive, guided workflow

</td>
<td width="50%">

### 🛠️ Without Claude

**Manual setup and customization**

1. **Clone and setup**
   ```bash
   git clone <your-repo>
   cd custom-mlflow-review-app
   ./setup.sh  # Interactive wizard
   ```

2. **Start development**
   ```bash
   ./watch.sh  # Starts servers
   # Frontend: http://localhost:5173
   # Backend: http://localhost:8000
   ```

3. **Customize manually:**
   - Edit `config.yaml` for experiment
   - Use CLI tools to create schemas
   - Set up labeling sessions
   - Deploy when ready

**You'll need to edit:**
- `config.yaml` - Set experiment ID
- `server/routers/` - Add API endpoints
- `client/src/pages/` - Customize UI
- `tools/` - Create CLI tools

</td>
</tr>
</table>

## 🔧 Customization Guide

### 🤖 With Claude Code (AI-Powered)

Claude Code provides an intelligent 3-step workflow:

```
/review-app analyze my Unity Catalog agent for SQL accuracy
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Environment Setup → Automated setup.sh execution                  │
│  Step 2: Experiment Analysis → AI analyzes traces and patterns             │
│  Step 3: Labeling Optimization → Creates custom schemas automatically      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Claude Commands Available:**
- `/review-app` - Complete customization workflow
- `/label-schemas` - Manage labeling schemas interactively
- `/labeling-sessions` - Create and manage review sessions
- Natural language: "analyze my experiment", "create a rating schema", etc.

### 🛠️ Without Claude (Manual)

#### Step 1: Configure Experiment

Edit `config.yaml`:
```yaml
# MLflow experiment to review
mlflow:
  experiment_id: 'your_experiment_id_here'
  
# Custom thank you message for reviewers
sme_thank_you_message: |
  Thank you for reviewing our AI agent!
  Your feedback helps improve our system.
```

#### Step 2: Create Labeling Schemas

Use the CLI tools to create schemas:

```bash
# Numeric rating schema
./mlflow-cli run create_labeling_schemas \
  --name "Response Quality" \
  --type numeric \
  --min 1 --max 5 \
  --instruction "Rate the AI response quality"

# Categorical schema
./mlflow-cli run create_labeling_schemas \
  --name "Accuracy" \
  --type categorical \
  --categories "Correct,Partially Correct,Incorrect" \
  --instruction "Is the response accurate?"

# Text feedback schema
./mlflow-cli run create_labeling_schemas \
  --name "Comments" \
  --type text \
  --instruction "Additional feedback or observations"
```

#### Step 3: Set Up Labeling Sessions

Create review sessions for your SMEs:

```bash
# Create a new labeling session
./mlflow-cli run create_labeling_session \
  --name "Week 1 Review" \
  --users "expert1@company.com,expert2@company.com" \
  --schemas "Response Quality,Accuracy,Comments"

# Link traces to the session
./mlflow-cli run link_traces_to_session \
  --session-name "Week 1 Review" \
  --filter "tags.version = 'v1.2'" \
  --limit 100
```

## 📝 Key Files to Customize

### 🤖 With Claude Code

Claude will handle all customization automatically, but you can guide it:
- Tell Claude what kind of agent you have
- Describe your evaluation needs
- Specify any special requirements
- Claude edits all files for you

### 🛠️ Without Claude

You'll need to manually edit these files:

#### Configuration Files
- **`config.yaml`** - Set your MLflow experiment ID and messages
- **`.env.local`** - Databricks authentication (created by setup.sh)

#### Backend Customization
- **`server/routers/review/`** - Add custom API endpoints
- **`server/models/`** - Define new data models
- **`server/utils/sme_*.py`** - Add analysis utilities

#### Frontend Customization
- **`client/src/pages/LabelingPage.tsx`** - Main SME interface
- **`client/src/components/SMELabelingInterface.tsx`** - Labeling UI
- **`client/src/components/session-renderer/renderers/`** - Custom trace views

#### CLI Tools
- **`tools/`** - Create new CLI tools for your workflow
- **`cli.py`** - Register new tools in the CLI system

## 📊 Visual Schema Examples

Both Claude and manual users will create schemas that look like this:

### Numeric Rating
```
┌─────────────────────────────────────────────────────────────────┐
│ ● Response Quality                                           ▲ │
├─────────────────────────────────────────────────────────────────┤
│ Rate the quality of the AI response                             │
│                                                                 │
│ [     4.5     ] ◄─────────────────────► Min: 1.0, Max: 5.0    │
└─────────────────────────────────────────────────────────────────┘
```

### Categorical Selection
```
┌─────────────────────────────────────────────────────────────────┐
│ ● Helpfulness                                                ▲ │
├─────────────────────────────────────────────────────────────────┤
│ Was the response helpful?                                       │
│                                                                 │
│ ○ Very Helpful                                                  │
│ ○ Somewhat Helpful                                              │
│ ○ Not Helpful                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🧰 CLI Tools Reference

The app includes 30+ CLI tools for MLflow operations:

```bash
# List all available tools
./mlflow-cli list

# Get help for any tool
./mlflow-cli help [tool_name]

# Search for specific functionality
./mlflow-cli search "labeling"
```

### Essential Tools for Manual Setup

| Tool | Purpose | Example |
|------|---------|---------|
| `create_labeling_schemas` | Create evaluation schemas | `./mlflow-cli run create_labeling_schemas --name "Quality" --type numeric` |
| `create_labeling_session` | Create review session | `./mlflow-cli run create_labeling_session --name "Sprint 1"` |
| `link_traces_to_session` | Add traces to session | `./mlflow-cli run link_traces_to_session --session-id abc123` |
| `list_labeling_sessions` | View all sessions | `./mlflow-cli run list_labeling_sessions` |
| `analyze_labeling_results` | Analyze feedback | `./mlflow-cli run analyze_labeling_results --session-id abc123` |

## 🎨 Creating Custom Trace Renderers

### 🤖 With Claude Code

Tell Claude what kind of renderer you need:
```
Create a custom renderer for SQL agent traces that shows the query, 
results table, and execution time prominently
```

Claude will create the complete renderer for you.

### 🛠️ Without Claude

Create a new file in `client/src/components/session-renderer/renderers/`:

```typescript
// SQLAgentRenderer.tsx
import { ItemRenderer } from '@/types/renderers';

export const SQLAgentRenderer: ItemRenderer = {
  name: 'SQL Agent View',
  description: 'Optimized for SQL query evaluation',
  render: (item) => {
    // Extract data from the trace
    const query = item.source?.request?.messages?.[0]?.content || '';
    const results = item.source?.response?.choices?.[0]?.message?.content || '';
    
    return (
      <div className="space-y-4">
        <div className="bg-gray-100 p-4 rounded">
          <h3 className="font-bold">SQL Query:</h3>
          <pre className="mt-2">{query}</pre>
        </div>
        
        <div className="bg-blue-50 p-4 rounded">
          <h3 className="font-bold">Results:</h3>
          <div className="mt-2">{results}</div>
        </div>
        
        {/* Add evaluation UI here */}
      </div>
    );
  }
};
```

Then register it in `renderers/index.ts`:
```typescript
export const renderers = [
  DefaultItemRenderer,
  CompactTimelineRenderer,
  SQLAgentRenderer,  // Add your renderer
];
```

## 🚀 Deployment

### 🤖 With Claude Code

Simply tell Claude:
```
Deploy the app to Databricks
```

Claude will run `./deploy.sh` and verify deployment.

### 🛠️ Without Claude

```bash
# Deploy to existing app
./deploy.sh

# Create new app and deploy
./deploy.sh --create

# Deploy with verbose logging
./deploy.sh --verbose
```

## 📁 Project Structure

```
├── server/                    # FastAPI backend
│   ├── routers/              # API endpoints (customize here)
│   ├── models/               # Data models
│   └── utils/                # Utilities
│
├── client/                   # React frontend  
│   ├── src/
│   │   ├── pages/           # Main pages (customize UI here)
│   │   ├── components/      # Reusable components
│   │   └── session-renderer/ # Custom trace renderers
│
├── tools/                    # CLI tools (30+ tools)
│
├── scripts/                  # Dev scripts
│   ├── setup.sh             # Environment setup
│   ├── watch.sh             # Start dev servers
│   └── deploy.sh            # Deploy to Databricks
│
├── .claude/commands/         # Claude Code commands
│   └── review-app.md        # AI workflow definition
│
└── config.yaml              # Main configuration
```

## 🐛 Troubleshooting

### Common Issues

| Issue | With Claude | Without Claude |
|-------|------------|----------------|
| **Setup problems** | Claude runs setup.sh automatically | Run `./setup.sh` manually |
| **Dev server issues** | Tell Claude "restart the servers" | `pkill -f watch.sh && ./watch.sh` |
| **Auth errors** | Claude will fix it | Check `.env.local` and rerun `./setup.sh` |
| **Missing TypeScript client** | Claude regenerates it | `uv run python scripts/make_fastapi_client.py` |

### Getting Help

- **With Claude**: Just describe your problem in natural language
- **Without Claude**: Check logs at `/tmp/databricks-app-watch.log`

## 📖 Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Claude Code](https://claude.ai/code) - For AI-powered development

### Support
- **With Claude**: Claude provides interactive help and debugging
- **Without Claude**: Use GitHub issues or Databricks community forums

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./fix.sh` to format code
5. Submit a pull request

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🎯 Ready to evaluate your AI agents?                                      │
│                                                                             │
│  With Claude: /review-app                                                  │
│  Without Claude: ./setup.sh                                                │
│                                                                             │
│  Start customizing your review app today!                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```