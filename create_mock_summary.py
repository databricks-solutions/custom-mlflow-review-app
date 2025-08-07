#!/usr/bin/env python
"""Create a mock experiment summary to demonstrate the UI."""

import json
import os

# Mock experiment ID (use any valid ID from your workspace or keep the test one)
EXPERIMENT_ID = "735126582997352042"

# Create mock analysis result
mock_analysis = {
    "status": "success",
    "experiment_id": EXPERIMENT_ID,
    "metadata": {
        "analysis_timestamp": "2024-08-07T10:30:00",
        "model_endpoint": "databricks-claude-sonnet-4",
        "traces_analyzed": 50,
        "total_issues_found": 8,
        "critical_issues": 2,
        "high_priority_issues": 3,
        "schemas_generated": 7
    },
    "executive_summary": {
        "agent_type": "SQL Assistant - A conversational agent that helps users query and analyze database information",
        "total_traces_analyzed": 50,
        "critical_issues_found": 2,
        "high_priority_issues": 3,
        "recommended_schemas": 7,
        "discovery_method": "open-ended-chain-of-thought"
    },
    "content": """# 🔬 Experiment Analysis Report

**Experiment:** SQL Assistant Testing (ID: 735126582997352042)
**Generated:** 2024-08-07 10:30:00
**Analysis Method:** Open-Ended Chain-of-Thought Discovery
**Traces Analyzed:** 50

## 📊 Executive Summary

- **Total Traces Analyzed:** 50
- **Traces with Issues:** 23 (46%)
- **Unique Issue Types Found:** 8
- **Critical Issues:** 2
- **High Priority Issues:** 3
- **Evaluation Schemas Generated:** 7

## 🤖 Agent Analysis

### What This Agent Does
This is a SQL-powered conversational assistant that helps users query and analyze database information. The agent:
- Accepts natural language queries about data
- Translates them to SQL queries
- Executes queries against a database
- Returns formatted results to users

## 🚨 Quality Issues Found

### 🔴 Critical Severity Issues

#### SQL Syntax Errors
- **Type:** `sql_syntax_error`
- **Affected Traces:** 8 out of 50
- **Description:** Agent generates SQL queries with syntax errors that fail to execute
- **Example Problems:**
```sql
SELECT * FROM cusotmers WHERE 1=1  -- Typo in table name
```

### 🟠 High Severity Issues

#### Response Without Tool Usage
- **Type:** `hallucination_no_tool`
- **Affected Traces:** 5 out of 50
- **Description:** Agent provides specific data answers without actually querying the database
- **Example Problems:**
```
User: "What's our market share?"
Agent: "Our market share is 35%" (No SQL query executed)
```

#### Unfaithful Response
- **Type:** `response_mismatch`
- **Affected Traces:** 10 out of 50
- **Description:** Agent response doesn't accurately reflect the tool output

### 🟡 Medium Severity Issues

#### Connection Errors Not Handled
- **Type:** `error_handling`
- **Affected Traces:** 6 out of 50
- **Description:** Agent doesn't gracefully handle database connection errors

## 📋 Recommended Evaluation Schemas

### Human Feedback Schemas

🔥 **SQL Query Correctness**
- **Type:** numerical
- **Question:** Rate the correctness of the SQL query for the user's request
- **Traces Affected:** 23
- **Priority Score:** 95/100

🔥 **Response Faithfulness**
- **Type:** numerical
- **Question:** Does the response accurately reflect the database query results?
- **Traces Affected:** 15
- **Priority Score:** 90/100

📊 **Error Handling Quality**
- **Type:** categorical
- **Question:** How well does the agent handle errors?
- **Traces Affected:** 8
- **Priority Score:** 75/100

### Ground Truth Expectation Schemas

✅ **Expected: Correct SQL Query**
- **Type:** text
- **Question:** Provide the correct SQL query that should have been generated
- **Traces Affected:** 8
- **Priority Score:** 95/100

## 🔍 Detailed Analysis

### Discovery Process

This analysis used an open-ended discovery approach:
1. **Agent Understanding**: First analyzed sample traces to understand the agent's purpose and expected behavior
2. **Issue Discovery**: Identified quality issues specific to this agent and domain without using predefined categories
3. **Comprehensive Analysis**: Systematically analyzed all traces for discovered issue patterns
4. **Schema Generation**: Created evaluation schemas tailored to the specific issues found

## 📝 Next Steps

1. **Review Generated Schemas**: Examine the suggested evaluation schemas and save the ones relevant to your needs
2. **Create Labeling Sessions**: Set up labeling sessions with the saved schemas for SME evaluation
3. **Assign SMEs**: Assign subject matter experts to review traces with identified issues
4. **Iterate**: Use feedback to improve the agent and re-run analysis periodically

---

*This report was generated using open-ended AI analysis with chain-of-thought reasoning. All issues and schemas are derived from the actual trace data without predefined categories.*
""",
    "detected_issues": [
        {
            "issue_type": "sql_syntax_error",
            "severity": "critical",
            "title": "SQL Syntax Errors",
            "description": "Agent generates SQL queries with syntax errors",
            "affected_traces": 8,
            "example_traces": ["trace_001", "trace_015", "trace_023"],
            "all_trace_ids": ["trace_001", "trace_015", "trace_023", "trace_027", "trace_031", "trace_039", "trace_044", "trace_048"],
            "problem_snippets": ["SELECT * FROM cusotmers WHERE 1=1", "SELECT FROM products"]
        },
        {
            "issue_type": "hallucination_no_tool",
            "severity": "high",
            "title": "Response Without Tool Usage",
            "description": "Agent provides data without querying database",
            "affected_traces": 5,
            "example_traces": ["trace_003", "trace_012", "trace_025"],
            "all_trace_ids": ["trace_003", "trace_012", "trace_025", "trace_037", "trace_045"],
            "problem_snippets": ["Our market share is 35%", "Total revenue is $1.2M"]
        }
    ],
    "schemas_with_label_types": [
        {
            "key": "sql_query_correctness",
            "name": "SQL Query Correctness",
            "label_type": "FEEDBACK",
            "schema_type": "numerical",
            "description": "Rate the correctness of the SQL query for the user's request",
            "min": 1,
            "max": 5,
            "priority_score": 95,
            "affected_trace_count": 23,
            "all_affected_traces": ["trace_001", "trace_003", "trace_012", "trace_015", "trace_023"]
        },
        {
            "key": "correct_sql_query",
            "name": "Expected: Correct SQL Query",
            "label_type": "EXPECTATION",
            "schema_type": "text",
            "description": "Provide the correct SQL query that should have been generated",
            "max_length": 1000,
            "priority_score": 95,
            "affected_trace_count": 8,
            "all_affected_traces": ["trace_001", "trace_015", "trace_023", "trace_027"]
        }
    ],
    "has_summary": True,
    "source": "mock_analysis"
}

# Save as JSON for the UI to load
output_file = f"analysis_reports/{EXPERIMENT_ID}_summary.json"
os.makedirs("analysis_reports", exist_ok=True)

with open(output_file, "w") as f:
    json.dump(mock_analysis, f, indent=2)

print(f"✅ Mock summary created: {output_file}")
print(f"\nThe summary includes:")
print(f"- {mock_analysis['metadata']['traces_analyzed']} traces analyzed")
print(f"- {mock_analysis['metadata']['total_issues_found']} issues found")
print(f"- {mock_analysis['metadata']['schemas_generated']} schemas generated")
print(f"\nTo see this in the UI:")
print(f"1. The summary endpoint needs to read from this file")
print(f"2. Or trigger a real analysis with: POST /api/experiment-summary/trigger-analysis")