---
description: "Complete MLflow Review App setup and customization workflow"
---

# 🎯 Welcome to Your MLflow Review App!

```
╭─────────────────────────────────────────────────────────────────────────────╮
│                                                                             │
│   🎯 MLflow Review App - Complete Customization Workflow                   │
│                                                                             │
│   Transform your MLflow traces into a powerful evaluation platform!        │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯
```

Welcome to the **MLflow Review App** configuration: $ARGUMENTS

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

## 🔧 How I'll Help You Customize

I'll guide you through a **3-step personalization process**:

**Step 1: Environment Setup** → Ensure Databricks connection and dependencies  
**Step 2: Experiment Analysis** → AI-powered analysis of your traces and agent patterns  
**Step 3: Labeling Optimization** → Create schemas and sessions tailored to your use case  

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🎯 Ready to create your personalized evaluation platform?                 │
│     Let's start with environment setup...                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step 1: Environment Setup

First, I'll check if your environment is already configured:

**After checking your existing configuration, I'll always ask you:**

**"Would you like to run setup again, or continue with experiment analysis?"**

**This gives you two options:**
- **Run setup again** → Reconfigure authentication, experiment, permissions, dependencies
- **Continue with analysis** → Use current settings and proceed to experiment analysis

**I'll respect your choice regardless of whether you already have configuration files.**

**For new setup, I'll run:**
```bash
# Opens new terminal window and runs setup
if [ -d "/Applications/iTerm.app" ]; then
    osascript -e 'tell application "iTerm" to create window with default profile' \
              -e 'tell application "iTerm" to tell current session of current window to write text "cd '"$(pwd)"' && ./setup.sh --auto-close"' \
              -e 'tell application "iTerm" to activate'
else
    osascript -e 'tell application "Terminal" to do script "cd '"$(pwd)"' && ./setup.sh --auto-close"' \
              -e 'tell application "Terminal" to activate'
fi
```

**The setup script configures:**
- ✅ Databricks authentication (PAT or profile)
- ✅ Environment variables and credentials  
- ✅ MLflow experiment selection and permissions
- ✅ Python dependencies (uv) and frontend (bun)
- ✅ App deployment configuration

**If setup is needed, please let me know when the setup.sh script is complete so we can continue.**

## 🛠️ Development Environment Startup

After setup is complete, I'll start your development environment and open the app:

### Start Development Servers
```bash
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &
```
- **Frontend**: http://localhost:5173 (React + Vite)
- **Backend**: http://localhost:8000 (FastAPI)
- **Logs**: `tail -f /tmp/databricks-app-watch.log`

### Open App in Playwright
I'll navigate to your development app at `/dev` to show you the current state:
- Open **http://localhost:5173/dev** in Playwright browser
- Take screenshot of your current review app interface
- Show you what we're working with before customization

---

## 🧪 Step 2: Experiment Analysis & Optimization

With the app running, I'll help you analyze and optimize your MLflow experiment:

### Current Experiment Analysis
I'll analyze your experiment from `config.yaml` to understand:
- **Agent architecture** - Multi-agent vs single-agent patterns
- **Tool usage** - What capabilities your agent has
- **Interaction patterns** - How users engage with your agent
- **Evaluation opportunities** - What aspects need human review

### AI-Powered Recommendations  
I'll run comprehensive AI analysis to generate:
- **Suggested labeling schemas** tailored to your agent
- **Recommended evaluation criteria** based on actual usage
- **Labeling session strategies** for effective SME workflows
- **Custom thank you messages** for your reviewers

### Interactive Schema & Session Creation
After showing you the analysis recommendations, I'll ask:

**"Do you want me to create any of these labeling schemas or labeling sessions for you?"**

**If you say yes, I'll:**

1. **For each recommended schema:**
   - Show you the schema details (type, options, description)
   - Ask: "Create this schema?" with preview of how it appears in Databricks UI
   - If yes: Run `/label-schemas add [description]` with the AI-generated details
   - If no: Skip to next schema

2. **For each recommended labeling session:**
   - Show you the session plan (name, assigned users, linked schemas, trace criteria)
   - Ask: "Create this labeling session?" with preview of configuration
   - If yes: Run `/labeling-sessions add [description]` with the AI-generated plan
   - If no: Skip to next session

3. **After creating schemas/sessions:**
   - Use `/labeling-sessions` to show you what was created
   - Use `/label-schemas` to display the new schemas
   - Ask if you want to link traces to any new sessions
   - Provide URLs to open sessions in Databricks

**Other options:**
- **Customize recommendations** → Modify suggestions before creating
- **Skip for now** → Continue with manual setup in Step 3

### Interactive Experiment Selection
If you want to analyze a different experiment:
- Provide experiment ID or Databricks URL
- I'll extract the ID and validate access
- Update your `config.yaml` with the new experiment
- Re-run analysis for the new experiment

---

## 🏷️ Step 3: Labeling Infrastructure Setup

Based on the experiment analysis, I'll work with you to create optimized labeling infrastructure:

### Current Infrastructure Review
I'll use `/label-schemas` and `/labeling-sessions` to show your current setup:
- **Display existing schemas** with beautiful CLI formatting and visual representations
- **Show active sessions** with progress, assignments, and completion rates
- **Run comprehensive analysis** of current labeling results and patterns

### AI-Powered Schema Creation
Based on your agent analysis, I'll suggest and create tailored schemas:
- **Context-aware recommendations** specific to your agent type and capabilities
- **Interactive schema building** using `/label-schemas add` with natural language
- **Schema previews** showing exactly how they'll appear in the Databricks UI
- **Confirmation workflow** before creating each schema

### Intelligent Session Configuration
I'll help you create labeling sessions optimized for your experiment:
- **Trace selection strategies** using `/labeling-sessions link` with smart filtering
- **User assignment guidance** based on experiment complexity and evaluation needs  
- **Session organization** grouping related evaluations for better SME experience
- **Progress tracking setup** with completion monitoring and analytics

### Interactive Session Creation Workflow
I'll guide you through creating your first labeling session:

1. **Session Planning**: 
   - Analyze which traces need evaluation
   - Suggest appropriate schemas based on agent analysis
   - Recommend SME assignments

2. **Session Creation**:
   - Use `/labeling-sessions add` with natural language description
   - Preview session configuration before creation
   - Confirm trace selection and linking strategy

3. **Trace Linking**:
   - Use `/labeling-sessions link` with intelligent criteria
   - Preview traces that will be linked
   - Confirm final session setup

4. **Validation**:
   - Use `/labeling-sessions` to view the created session
   - Test session accessibility and SME workflow
   - Verify everything is ready for reviewers

---

## 🎯 Your Customized Review App

**After setup and optimization, you'll have:**

✅ **Fully configured environment** with Databricks integration  
✅ **Analyzed experiment** with comprehensive agent understanding  
✅ **Tailored labeling schemas** designed for your specific agent  
✅ **Optimized SME workflows** for effective evaluation  
✅ **Ready-to-use review app** for collecting human feedback

**Next steps:** I can help you deploy the app, create labeling sessions, or make additional customizations based on your specific needs.