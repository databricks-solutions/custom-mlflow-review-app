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

**🛑 CRITICAL: I MUST STOP AND WAIT FOR YOUR RESPONSE**

**After checking your existing configuration, I will ALWAYS pause and ask you:**

**"Would you like to run setup again, or continue with experiment analysis?"**

**I will NOT make this decision for you. I will:**
- ✅ **Show you the options clearly**
- ✅ **Wait for your explicit choice**
- ✅ **Only proceed after you respond**
- ❌ **NEVER assume what you want**
- ❌ **NEVER continue without your input**

**This gives you two options:**
- **Run setup again** → Reconfigure authentication, experiment, permissions, dependencies
- **Continue with analysis** → Use current settings and proceed to experiment analysis

**I'll respect your choice regardless of whether you already have configuration files.**

**For new setup, I'll launch the setup script in a new terminal:**
```bash
# Opens new terminal window and runs setup (non-blocking)
if [ -d "/Applications/iTerm.app" ]; then
    osascript -e 'tell application "iTerm" to create window with default profile' \
              -e 'tell application "iTerm" to tell current session of current window to write text "cd '"$(pwd)"' && ./setup.sh --auto-close"' \
              -e 'tell application "iTerm" to activate' &
else
    osascript -e 'tell application "Terminal" to do script "cd '"$(pwd)"' && ./setup.sh --auto-close"' \
              -e 'tell application "Terminal" to activate' &
fi
```

**The setup script will configure:**
- ✅ Databricks authentication (PAT or profile)
- ✅ Environment variables and credentials  
- ✅ MLflow experiment selection and permissions
- ✅ Python dependencies (uv) and frontend (bun)
- ✅ App deployment configuration

**🛑 IMPORTANT: I will launch the terminal and then immediately prompt you:**

**"I've opened the setup script in a new terminal. Please complete the setup process and let me know when you're done so we can continue with the next step."**

**I will wait for your response before proceeding - the setup script may take a few minutes to complete.**

## 🏥 Step 1.5: Deployment Health Check

After setup is complete, I'll verify your deployed app is healthy before proceeding:

### Check App Status & URL
```bash
# Get current app status and URL
uv run python app_status.py --format json
```

This will show me:
- ✅ **App URL** - Your deployed Databricks Apps URL  
- ✅ **Deployment status** - Whether the app is running
- ✅ **Permissions** - App access and user permissions

### Test API Health Endpoints
```bash
# Get the app URL first
APP_URL=$(uv run python app_status.py --format json | jq -r '.app_status.url')

# Test core health endpoints
uv run python dba_client.py $APP_URL /health
uv run python dba_client.py $APP_URL /api/user/me  
uv run python dba_client.py $APP_URL /api/config
```

**Expected responses:**
- `/health` → `{"status": "healthy"}`
- `/api/user/me` → Your user information
- `/api/config` → App configuration details

### Verify API Documentation
```bash
# Test that FastAPI docs are accessible
uv run python dba_client.py $APP_URL /docs
```

**🛑 IMPORTANT: I will present the results to you:**

**"✅ Your app is deployed and healthy at: [APP_URL]**  
**All health checks passed. Would you like to continue with the development environment setup?"**

**I will wait for your confirmation before proceeding with local development servers.**

**If any health checks fail, I'll help you troubleshoot the deployment before continuing.**

---

## 🛠️ Development Environment Startup

After confirming your deployment is healthy, I'll start your development environment:

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
I'll analyze your experiment from `.env.local` to understand:
- **Agent architecture** - Multi-agent vs single-agent patterns
- **Tool usage** - What capabilities your agent has
- **Interaction patterns** - How users engage with your agent
- **Evaluation opportunities** - What aspects need human review

### Current Infrastructure Review
First, I'll check your existing labeling infrastructure:
```bash
# List current labeling schemas and sessions
./mlflow-cli list labeling_sessions
./mlflow-cli list labeling_schemas
```

This shows me:
- **Existing labeling schemas** with visual representations
- **Active labeling sessions** with progress and assignments  
- **Current infrastructure gaps** that need to be filled

### AI-Powered Recommendations  
I'll run comprehensive AI analysis to generate tailored recommendations:
```bash
# Run AI analysis on your experiment (this may take 1-2 minutes)
./mlflow-cli run ai_analyze_experiment
```

**🛑 IMPORTANT: I will wait for the AI analysis to complete before proceeding.**

The analysis will generate:
- **Suggested labeling schemas** tailored to your specific agent
- **Recommended evaluation criteria** based on actual trace patterns
- **Labeling session strategies** for effective SME workflows
- **Custom thank you messages** for your reviewers

**After the analysis completes, I'll present all recommendations to you before proceeding.**

### User Decision Point

**🛑 CRITICAL: I MUST STOP AND WAIT FOR YOUR RESPONSE**

After showing you the analysis recommendations, I will present these options:

**"Based on the AI analysis, I have recommendations for labeling schemas and sessions. What would you like me to do?"**

**Option 1:** "Yes, create schemas" - I'll create the recommended labeling schemas

**Option 2:** "Yes, create sessions" - I'll create the recommended labeling sessions

**Option 3:** "Create both" - I'll create both schemas AND sessions

**Option 4:** "Let me review first" - Show more details before deciding

**Option 5:** "Skip for now" - Continue with manual setup guidance

### Interactive Schema & Session Creation

**I will NOT proceed without your explicit approval. I will:**
- ✅ **Show you all recommendations first**
- ✅ **Wait for your decision on each item**
- ✅ **Only create what you explicitly approve**
- ❌ **NEVER auto-create schemas or sessions**
- ❌ **NEVER assume you want anything created**

**If you say yes, I'll:**

1. **For each recommended schema:**
   - Show you the schema details (type, options, description)
   - **🛑 PAUSE AND ASK:** "Create this schema?" with preview of how it appears in Databricks UI
   - **WAIT FOR YOUR RESPONSE** before proceeding
   - If yes: Run `/label-schemas add [description]` with the AI-generated details
   - If no: Skip to next schema

2. **For each recommended labeling session:**
   - Show you the session plan (name, assigned users, linked schemas, trace criteria)
   - **🛑 PAUSE AND ASK:** "Create this labeling session?" with preview of configuration
   - **WAIT FOR YOUR RESPONSE** before proceeding  
   - If yes: Run `/labeling-sessions add [description]` with the AI-generated plan
   - If no: Skip to next session

3. **After creating schemas/sessions:**
   - Use `/labeling-sessions` to show you what was created
   - Use `/label-schemas` to display the new schemas
   - **🛑 PAUSE AND ASK:** "Do you want to link traces to any new sessions?"
   - **WAIT FOR YOUR RESPONSE** before proceeding with trace linking
   - Provide URLs to open sessions in Databricks

**Other options:**
- **Customize recommendations** → Modify suggestions before creating
- **Skip for now** → Continue with manual setup in Step 3

### Interactive Experiment Selection
If you want to analyze a different experiment:
- Provide experiment ID or Databricks URL
- I'll extract the ID and validate access
- Update your `.env.local` with the new experiment
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