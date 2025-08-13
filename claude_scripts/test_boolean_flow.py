#!/usr/bin/env python3
"""Test end-to-end boolean flow: log feedback and verify it comes back as boolean."""

import requests
import json
import time

def test_boolean_flow():
    """Test logging boolean feedback and retrieving it."""
    
    base_url = "http://localhost:8000"
    trace_id = "tr-0de73a5cfc4e63469900392a8242824f"
    
    print("Testing boolean feedback flow...")
    
    # Step 1: Log feedback with boolean True (no quotes)
    print("\n1. Logging feedback with boolean True value...")
    payload = {
        "assessment": {
            "name": "test_boolean_flow",
            "value": True,  # Actual boolean, not string
            "rationale": "Testing boolean preservation"
        }
    }
    
    response = requests.post(
        f"{base_url}/api/mlflow/traces/{trace_id}/feedback",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Logged successfully: {result.get('assessment_id')}")
    else:
        print(f"   ❌ Failed to log: {response.status_code} - {response.text}")
        return
    
    # Give it a moment to propagate
    time.sleep(1)
    
    # Step 2: Get trace via REST API to check the assessment
    print("\n2. Retrieving trace to check assessment value...")
    response = requests.get(f"{base_url}/api/mlflow/traces/{trace_id}")
    
    if response.status_code == 200:
        trace_data = response.json()
        assessments = trace_data.get('info', {}).get('assessments', [])
        
        # Find our test assessment
        test_assessment = None
        for assessment in assessments:
            if assessment.get('name') == 'test_boolean_flow':
                test_assessment = assessment
                break
        
        if test_assessment:
            value = test_assessment.get('value')
            print(f"   Assessment value: {value}")
            print(f"   Type: {type(value)}")
            if value is True:
                print("   ✅ PASS: Value is boolean True")
            else:
                print(f"   ❌ FAIL: Value is {value} (type: {type(value)}), expected boolean True")
        else:
            print("   ⚠️ Test assessment not found")
    else:
        print(f"   ❌ Failed to get trace: {response.status_code}")
    
    # Step 3: Check labeling items to see how it's stored there
    print("\n3. Checking labeling items API...")
    review_app_id = "36cb6150924443a9a8abf3209bcffaf8"
    session_id = "54c766f8-7c10-4da2-9501-5a7e350e68a6"
    
    response = requests.get(
        f"{base_url}/api/review-apps/{review_app_id}/labeling-sessions/{session_id}/items"
    )
    
    if response.status_code == 200:
        items_data = response.json()
        items = items_data.get('items', [])
        
        # Find the item with our trace
        for item in items:
            if item.get('source', {}).get('trace_id') == trace_id:
                labels = item.get('labels', {})
                if 'test_boolean_flow' in labels:
                    label_value = labels['test_boolean_flow']
                    if isinstance(label_value, dict):
                        value = label_value.get('value')
                    else:
                        value = label_value
                    
                    print(f"   Label value in items: {value}")
                    print(f"   Type: {type(value)}")
                    if value is True:
                        print("   ✅ PASS: Label value is boolean True")
                    elif value == 1:
                        print("   ❌ FAIL: Label value is numeric 1, should be boolean True")
                    else:
                        print(f"   ❌ FAIL: Label value is {value} (type: {type(value)})")
                else:
                    print("   ⚠️ test_boolean_flow label not found in item")
                break
        else:
            print(f"   ⚠️ Item with trace {trace_id} not found")
    else:
        print(f"   ❌ Failed to get items: {response.status_code}")

if __name__ == "__main__":
    test_boolean_flow()