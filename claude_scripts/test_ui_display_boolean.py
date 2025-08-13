#!/usr/bin/env python3
"""Test script to check how boolean values appear in UI display."""

import requests
import json

def test_trace_with_assessments():
    """Get a trace with assessments to see how values are displayed."""
    
    trace_id = "tr-c9ba18c61e323bb6c7375d11cd297eea" 
    base_url = "http://localhost:8000"
    
    print("Testing trace assessment display...")
    
    try:
        # Get trace with assessments
        print("\n1. Getting trace data...")
        response = requests.get(f"{base_url}/api/mlflow/traces/{trace_id}")
        
        if response.status_code == 200:
            trace_data = response.json()
            assessments = trace_data.get('info', {}).get('assessments', [])
            print(f"   Found {len(assessments)} assessments")
            
            # Look for boolean assessments
            for assessment in assessments:
                name = assessment.get('name', '')
                value = assessment.get('value')
                assessment_type = assessment.get('type', 'unknown')
                print(f"   Assessment '{name}': {repr(value)} (type: {type(value).__name__}, assessment_type: {assessment_type})")
                
                # Check if this is a boolean that might be displayed as 1/0
                if isinstance(value, bool):
                    print(f"     ✓ Boolean value correctly preserved: {value}")
                elif isinstance(value, (int, float)) and value in [0, 1]:
                    print(f"     ⚠️  Numeric value that might be boolean: {value}")
                elif isinstance(value, str) and value.lower() in ['true', 'false']:
                    print(f"     ⚠️  String value that might be boolean: '{value}'")
                    
        else:
            print(f"   Error: {response.status_code} - {response.text}")
            
        # Also test trace metadata endpoint
        print("\n2. Getting trace metadata...")
        response = requests.get(f"{base_url}/api/mlflow/traces/{trace_id}/metadata")
        
        if response.status_code == 200:
            metadata = response.json()
            print(f"   Metadata keys: {list(metadata.keys())}")
            if 'info' in metadata and 'assessments' in metadata['info']:
                assessments = metadata['info']['assessments']
                print(f"   Assessments in metadata: {len(assessments)}")
                for assessment in assessments:
                    name = assessment.get('name', '')
                    value = assessment.get('value')
                    print(f"     Metadata assessment '{name}': {repr(value)} (type: {type(value).__name__})")
        else:
            print(f"   Metadata error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trace_with_assessments()