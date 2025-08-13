# 🎯 MLflow Review App - Custom Evaluation Framework

![Databricks Apps](https://img.shields.io/badge/Databricks-Apps-orange)
![MLflow](https://img.shields.io/badge/MLflow-Integration-red)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![React](https://img.shields.io/badge/React-18+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)
![Claude](https://img.shields.io/badge/Claude_Code-Ready-purple)

Transform MLflow traces into a powerful human evaluation platform with custom schemas, SME workflows, and analytics.

## ✨ What's New

- 🌙 **Dark Mode** - Professional DuBois theme with light/dark toggle
- 💾 **Auto-Save** - Real-time save indicators replace toast notifications
- 📝 **MLflow Feedback API** - Direct feedback logging with `log_feedback` and `log_expectation`
- 🔍 **Enhanced Trace Search** - Improved filtering and pagination in Add Traces modal
- 🎨 **New Renderers** - ToolRenderer for specialized trace visualization
- 🛠️ **Simplified User Management** - New `set_labeling_session_users` CLI tool

## 🚀 Quick Start

### Prerequisites

```bash
# Install required tools
curl -LsSf https://astral.sh/uv/install.sh | sh  # Python package manager
curl -fsSL https://bun.sh/install | bash          # JavaScript package manager
brew install databricks                           # Databricks CLI
```

### Choose Your Path

#### 🤖 AI-Powered Setup (Claude Code)

```
/review-app analyze my SQL agent
```

Claude handles everything automatically:
- ✅ Environment setup
- ✅ Experiment analysis
- ✅ Custom schema creation
- ✅ Session configuration
- ✅ Deployment

#### 🛠️ Manual Setup

```bash
./setup.sh   # Interactive setup wizard
./watch.sh   # Start dev servers (frontend:5173, backend:8000)
```

Then customize `config.yaml` and use CLI tools to configure your review app.

## 📦 Key Features

- **Custom Evaluation Schemas** - Mix ratings, categories, and text feedback
- **SME Assignment & Workflows** - Route traces to subject matter experts with progress tracking
- **Auto-Save UI** - Real-time feedback persistence with visual indicators
- **Dark Mode Support** - Professional theme system with user preference persistence
- **Analytics Dashboard** - Inter-rater agreement, feedback patterns, statistical analysis
- **MLflow Integration** - Direct trace access, feedback logging, experiment management
- **Custom Renderers** - Create specialized views for different agent types
- **30+ CLI Tools** - Complete toolkit for review app management

## 🎨 Customization Guide

### Configure Your Experiment

Edit `config.yaml`:
```yaml
mlflow:
  experiment_id: 'your_experiment_id'
  
sme_thank_you_message: |
  Thank you for reviewing our AI agent!
  Your feedback helps improve our system.
```

### Create Evaluation Schemas

```bash
# Use presets for quick setup
./mlflow-cli run create_labeling_schemas --preset quality-helpfulness

# Or create custom schemas
./mlflow-cli run create_labeling_schemas \
  --name "Accuracy" \
  --type categorical \
  --categories "Correct,Partial,Incorrect" \
  --instruction "Assess response accuracy"
```

### Set Up Review Sessions

```bash
# Create session with assigned reviewers
./mlflow-cli run create_labeling_session \
  --name "Week 1 Review" \
  --users "expert1@company.com,expert2@company.com"

# Link traces to session
./mlflow-cli run link_traces_to_session \
  --session-name "Week 1 Review" \
  --filter "tags.version = 'v1.2'" \
  --limit 100
```

### Create Custom Trace Renderers

Add specialized views in `client/src/components/session-renderer/renderers/`:

```typescript
export const SQLAgentRenderer: ItemRenderer = {
  name: 'SQL Agent View',
  description: 'Optimized for SQL query evaluation',
  render: (item) => (
    <div className="space-y-4">
      <QueryDisplay query={item.source?.request} />
      <ResultsTable results={item.source?.response} />
      <EvaluationForm schemas={item.schemas} />
    </div>
  )
};
```

## 🧰 Essential CLI Tools

| Tool | Purpose |
|------|---------|
| `create_labeling_schemas` | Define evaluation criteria (ratings, categories, text) |
| `create_labeling_session` | Set up review batches with assigned users |
| `link_traces_to_session` | Add traces for review with filters |
| `set_labeling_session_users` | Update session reviewer assignments |
| `log_feedback` | Send feedback directly to MLflow |
| `log_expectation` | Log expectations for trace evaluation |
| `analyze_labeling_results` | Statistical analysis of feedback |
| `ai_analyze_experiment` | AI-powered experiment analysis |

Full list with 30+ tools: `./mlflow-cli list`

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
├── tools/                    # CLI tools (30+ tools)
├── scripts/                  # Dev automation
│   ├── setup.sh             # Environment setup
│   ├── watch.sh             # Start dev servers
│   └── deploy.sh            # Deploy to Databricks
│
└── config.yaml              # Main configuration
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Dev server issues | `pkill -f watch.sh && ./watch.sh` |
| Auth errors | Re-run `./setup.sh` |
| Missing TypeScript client | `uv run python scripts/make_fastapi_client.py` |
| Deployment failures | Check logs with `dba_logz.py` |
| API 404 errors | Verify router registration in `server/app.py` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./fix.sh` to format code
5. Submit a pull request

## 📖 Resources

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Claude Code](https://claude.ai/code) - For AI-powered development

---

Ready to evaluate your AI agents? Start with `./setup.sh` or `/review-app` in Claude Code.