#!/usr/bin/env python3
"""Test script to verify MLflow boolean handling."""

import os
import mlflow
from mlflow.entities import AssessmentSource

# Set up environment 
os.environ['MLFLOW_EXPERIMENT_ID'] = '2178582188830602'

# Need to set auth environment variables too
import subprocess
result = subprocess.run(['source', '.env.local'], shell=True, capture_output=True, text=True)
# Load environment variables manually
env_vars = {}
try:
    with open('.env.local', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env.local not found")
    pass

def test_boolean_feedback():
    """Test logging boolean feedback values to MLflow."""
    
    # Use a known trace ID from your experiment
    trace_id = "tr-c9ba18c61e323bb6c7375d11cd297eea"
    
    print("Testing boolean feedback logging to MLflow...")
    
    try:
        # Test logging True
        print("\n1. Logging boolean True value...")
        assessment_true = mlflow.log_feedback(
            trace_id=trace_id,
            name="test_boolean_true",
            value=True,  # Actual boolean
            source=AssessmentSource(source_type='human', source_id='test_user'),
            metadata={'test': 'boolean_true'}
        )
        print(f"   Logged assessment ID: {assessment_true.assessment_id}")
        
        # Test logging False
        print("\n2. Logging boolean False value...")
        assessment_false = mlflow.log_feedback(
            trace_id=trace_id,
            name="test_boolean_false", 
            value=False,  # Actual boolean
            source=AssessmentSource(source_type='human', source_id='test_user'),
            metadata={'test': 'boolean_false'}
        )
        print(f"   Logged assessment ID: {assessment_false.assessment_id}")
        
        # Now retrieve the trace and check what values were actually stored
        print("\n3. Retrieving trace to check stored values...")
        trace = mlflow.get_trace(trace_id)
        
        if hasattr(trace.info, 'assessments') and trace.info.assessments:
            print(f"   Found {len(trace.info.assessments)} assessments on trace")
            for assessment in trace.info.assessments:
                if hasattr(assessment, 'name'):
                    if assessment.name in ['test_boolean_true', 'test_boolean_false']:
                        print(f"   Assessment '{assessment.name}':")
                        if hasattr(assessment, 'feedback') and assessment.feedback:
                            value = assessment.feedback.value
                            print(f"     Value: {value} (type: {type(value)})")
                        elif hasattr(assessment, 'value'):
                            value = assessment.value
                            print(f"     Value: {value} (type: {type(value)})")
        else:
            print("   No assessments found on trace")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_boolean_feedback()