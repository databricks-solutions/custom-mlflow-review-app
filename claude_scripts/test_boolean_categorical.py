#!/usr/bin/env python
"""
Test that boolean categorical values are sent as actual booleans.
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_boolean_categorical():
    print("Testing boolean categorical conversion...")
    
    # Get a trace
    search_payload = {"experiment_ids": [], "max_results": 1}
    response = requests.post(f"{BASE_URL}/api/mlflow/search-traces", json=search_payload)
    traces = response.json().get("traces", [])
    if not traces:
        print("❌ No traces found")
        return False
    
    trace_id = traces[0]["info"]["trace_id"]
    print(f"Using trace: {trace_id}")
    
    # Test True value from categorical
    print("\nTesting categorical 'True' -> boolean true...")
    response = requests.post(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json={
            "assessment": {
                "name": "test_cat_bool_true",
                "value": True,  # Should be actual boolean
                "rationale": "Testing categorical True as boolean"
            }
        }
    )
    
    if response.status_code == 200:
        print("✅ True boolean sent successfully")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Test False value from categorical  
    print("\nTesting categorical 'False' -> boolean false...")
    response = requests.post(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json={
            "assessment": {
                "name": "test_cat_bool_false", 
                "value": False,  # Should be actual boolean
                "rationale": "Testing categorical False as boolean"
            }
        }
    )
    
    if response.status_code == 200:
        print("✅ False boolean sent successfully")
    else:
        print(f"❌ Failed: {response.text}")
        return False
    
    # Verify the values are stored as booleans
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/api/mlflow/traces/{trace_id}/metadata")
    if response.status_code == 200:
        metadata = response.json()
        assessments = metadata.get("info", {}).get("assessments", [])
        
        true_assessment = next((a for a in assessments if a.get("name") == "test_cat_bool_true"), None)
        false_assessment = next((a for a in assessments if a.get("name") == "test_cat_bool_false"), None)
        
        if true_assessment and true_assessment.get("value") is True:
            print("✅ True value stored as boolean")
        else:
            print(f"❌ True value not stored correctly: {true_assessment}")
            return False
            
        if false_assessment and false_assessment.get("value") is False:
            print("✅ False value stored as boolean")
        else:
            print(f"❌ False value not stored correctly: {false_assessment}")
            return False
    
    print("\n✅ Boolean categorical conversion test passed!")
    return True

if __name__ == "__main__":
    success = test_boolean_categorical()
    exit(0 if success else 1)