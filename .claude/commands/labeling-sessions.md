# Labeling Sessions Management

Manage labeling sessions for your MLflow Review App. This command helps you view, create, modify, and delete sessions interactively.

## Usage

```bash
/labeling-sessions [action]
```

## Actions

### List Sessions (default)
```bash
/labeling-sessions
```
Shows all current labeling sessions with details about assigned users, schemas, linked traces, and session status.

**Intelligent Context**: References experiment summaries from `experiments/[experiment_id]_summary.md` to provide context about what type of agent is being evaluated in each session.

### Add New Session
```bash
/labeling-sessions add [description]
```

Examples:
- `/labeling-sessions add "Quality Review Session" with users john@company.com, jane@company.com`
- `/labeling-sessions add "June Evaluation" for reviewer@company.com using quality and helpfulness schemas`
- `/labeling-sessions add session from file session_config.json`

**Context-Driven Session Design**: Uses experiment analysis to suggest:
- **Targeted trace selection**: Based on agent capabilities and use cases
- **Appropriate schemas**: Matching agent complexity and evaluation needs
- **Session focus areas**: Highlighting key evaluation criteria from experiment summaries

### Modify Session
```bash
/labeling-sessions modify [session_name] [changes]
```

Examples:
- `/labeling-sessions modify "Quality Review" add user alice@company.com`
- `/labeling-sessions modify "June Evaluation" remove helpfulness schema`
- `/labeling-sessions modify "Test Session" change name to "Production Review"`

### Delete Session
```bash
/labeling-sessions delete [session_name]
```

Examples:
- `/labeling-sessions delete "Test Session"`
- `/labeling-sessions delete "Old Review"`

### Link Traces
```bash
/labeling-sessions link [session_name] [trace_criteria]
```

Examples:
- `/labeling-sessions link "Quality Review" traces from last week`
- `/labeling-sessions link "Test Session" traces with tag.model = "gpt-4"`
- `/labeling-sessions link "June Evaluation" 10 random traces`

### Analyze Results
```bash
/labeling-sessions analyze [session_name_or_filter]
```

Examples:
- `/labeling-sessions analyze` - Analyze all sessions with statistical summaries
- `/labeling-sessions analyze "Quality Review"` - Analyze specific session
- `/labeling-sessions analyze state=COMPLETED` - Analyze only completed sessions
- `/labeling-sessions analyze --session-id abc123` - Analyze by session ID

## Implementation

This command orchestrates the following tools:
- `tools/list_labeling_sessions.py` - List current sessions (includes auto-analysis)
- `tools/create_labeling_session.py` - Create new sessions
- `tools/update_labeling_session.py` - Modify existing sessions
- `tools/delete_labeling_session.py` - Delete sessions
- `tools/link_traces_to_session.py` - Link traces to sessions
- `tools/analyze_labeling_results.py` - Analyze session results with statistical summaries
- `tools/get_labeling_session_urls.py` - Get session URLs for opening in browser

All tools use shared utilities in `server/utils/labeling_sessions_utils.py` for consistent API access.

## Workflow

1. **List**: Display current sessions with beautiful CLI formatting showing:
   - Session name, ID, and description
   - Assigned users
   - Active schemas
   - Number of linked traces
   - Creation and update timestamps
   - **Auto-analysis results**: completion rates, statistical summaries per schema, key insights
   - Direct links to open in Databricks
   - **CRITICAL WORKFLOW**: When listing sessions, ALWAYS run the Complete Labeling Results Analysis System:
     1. **Execute Tool**: Run `list_labeling_sessions.py` which returns deterministic JSON with analysis data
     2. **Claude Analysis**: Read the JSON output and create a comprehensive, beautiful summary report:
        - **Overall Status**: Total sessions, completion rates, engagement metrics across all sessions
        - **Assessment-Oriented Analysis**: For each assessment schema in each session:
          - Statistical summaries (distributions, averages, consensus levels)
          - SME response patterns and feedback themes
          - Trace content correlation analysis (what parts of traces drove SME decisions)
          - Visual representations with emojis, progress bars, and charts
        - **Pattern Detection**: Identify correlations between trace content and assessment outcomes
        - **Actionable Insights**: Key findings, recommendations, sessions needing attention
        - **Next Steps**: Specific actions to improve completion rates and assessment quality

2. **Add**: Parse natural language, validate users and schemas, show preview, ask for confirmation, then create

3. **Modify**: Parse changes, show what will change, ask for confirmation, then update

4. **Delete**: Show what will be deleted (including linked traces info), ask for confirmation, then remove

5. **Link**: Search for traces based on criteria, show preview of traces to be linked, ask for confirmation, then link

6. **Analyze**: Generate comprehensive statistical analysis of SME labeling results:
   - **Categorical schemas**: Count/percentage distributions, consensus analysis
   - **Numeric schemas**: Mean, median, std deviation, range, distribution bins
   - **Text schemas**: Response length analysis, common themes, sample responses
   - **Key insights**: Automated detection of patterns, outliers, and recommendations

## Confirmations

All actions require explicit user confirmation:
- Show exactly what will be created/changed/deleted
- Display impact (e.g., "This will link 15 traces to the session")
- Ask user to type specific confirmation phrase
- Only proceed after confirmation received

## Session Status Display

Sessions are displayed with rich information:
```
📋 Quality Review Session
   🆔 ID: abc123-def456
   👥 Users: john@company.com, jane@company.com  
   🏷️  Schemas: quality_rating, helpfulness
   🔗 Linked Traces: 25
   📅 Created: 2024-01-15 by john@company.com
   🌐 Open in Databricks: [Click here]
```