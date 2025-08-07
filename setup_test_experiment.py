#!/usr/bin/env python
"""Set up a test experiment with sample traces and run analysis."""

import os
import json
import time
import mlflow
from mlflow.tracking import MlflowClient

# Create or get test experiment
client = MlflowClient()
experiment_name = "AI Assistant Testing"

try:
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment:
        experiment_id = experiment.experiment_id
        print(f"Using existing experiment: {experiment_id}")
    else:
        experiment_id = client.create_experiment(experiment_name)
        print(f"Created new experiment: {experiment_id}")
except:
    experiment_id = client.create_experiment(experiment_name + "_" + str(int(time.time())))
    print(f"Created new experiment with timestamp: {experiment_id}")

# Log some sample traces
mlflow.set_experiment(experiment_name)

# Sample trace 1: Successful query
with mlflow.start_run() as run:
    mlflow.log_param("trace_type", "test")
    
    # Create a trace-like structure
    trace_data = {
        "request": "What are the top 5 products by revenue?",
        "response": "Here are the top 5 products by revenue:\n1. Product A - $1.2M\n2. Product B - $980K...",
        "tool_calls": [{
            "tool": "sql_query",
            "query": "SELECT product_name, SUM(revenue) as total FROM sales GROUP BY product_name ORDER BY total DESC LIMIT 5",
            "result": "5 rows returned"
        }]
    }
    
    # Log as artifact (simulating trace storage)
    with open("/tmp/trace1.json", "w") as f:
        json.dump(trace_data, f)
    mlflow.log_artifact("/tmp/trace1.json", "traces")
    
    mlflow.log_metric("execution_time_ms", 1250)
    mlflow.set_tag("trace_status", "success")

# Sample trace 2: Query with error
with mlflow.start_run() as run:
    mlflow.log_param("trace_type", "test")
    
    trace_data = {
        "request": "Show me customer demographics",
        "response": "I'll analyze the customer demographics for you.",
        "tool_calls": [{
            "tool": "sql_query", 
            "query": "SELECT * FROM cusotmers WHERE 1=1",  # Typo in table name
            "error": "Table 'cusotmers' not found"
        }]
    }
    
    with open("/tmp/trace2.json", "w") as f:
        json.dump(trace_data, f)
    mlflow.log_artifact("/tmp/trace2.json", "traces")
    
    mlflow.log_metric("execution_time_ms", 850)
    mlflow.set_tag("trace_status", "error")

# Sample trace 3: Hallucination case
with mlflow.start_run() as run:
    mlflow.log_param("trace_type", "test")
    
    trace_data = {
        "request": "What's our market share?",
        "response": "Our market share is approximately 35% in the North American region.",
        "tool_calls": []  # No tool was called but agent made up a number
    }
    
    with open("/tmp/trace3.json", "w") as f:
        json.dump(trace_data, f)
    mlflow.log_artifact("/tmp/trace3.json", "traces")
    
    mlflow.log_metric("execution_time_ms", 500)
    mlflow.set_tag("trace_status", "success")
    mlflow.set_tag("potential_issue", "hallucination")

print(f"\n✅ Setup complete!")
print(f"Experiment ID: {experiment_id}")
print(f"\nTo use this experiment:")
print(f"1. Add to .env.local:")
print(f"   MLFLOW_EXPERIMENT_ID={experiment_id}")
print(f"2. Restart the dev server")
print(f"3. Trigger analysis from the UI or API")