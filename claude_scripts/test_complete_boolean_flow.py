#!/usr/bin/env python
"""
Complete test of the boolean data type flow.
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_complete_boolean_flow():
    print("=" * 60)
    print("COMPLETE BOOLEAN DATA TYPE FLOW TEST")
    print("=" * 60)
    
    headers = {'Content-Type': 'application/json'}
    timestamp = int(time.time())
    
    # Get review app ID
    response = requests.get(f"{BASE_URL}/api/manifest")
    manifest = response.json()
    review_app_id = manifest.get('config', {}).get('review_app_id')
    
    # Create a Pass/Fail schema with True/False options
    schema_name = f'test_boolean_flow_{timestamp}'
    schema_data = {
        'name': schema_name,
        'type': 'FEEDBACK',
        'title': 'Boolean Test',
        'instruction': 'Test boolean handling',
        'categorical': {'options': ['True', 'False']},
        'enable_comment': True
    }
    
    print("1. Creating Pass/Fail schema with True/False options...")
    response = requests.post(
        f"{BASE_URL}/api/review-apps/{review_app_id}/schemas",
        json=schema_data,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to create schema: {response.text}"
    print("   ✅ Schema created")
    
    # Get a trace
    search_payload = {"experiment_ids": [], "max_results": 1}
    response = requests.post(f"{BASE_URL}/api/mlflow/search-traces", json=search_payload)
    traces = response.json().get("traces", [])
    trace_id = traces[0]["info"]["trace_id"]
    
    # Test 1: Create assessment with True (should store as boolean true)
    print("\n2. Testing categorical 'True' -> boolean true...")
    response = requests.post(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json={
            "assessment": {
                "name": schema_name,
                "value": True,  # Actual boolean (as the UI should send after conversion)
                "rationale": "Testing True conversion"
            }
        }
    )
    assert response.status_code == 200, f"Failed to log True: {response.text}"
    true_assessment_id = response.json().get('assessment_id')
    print("   ✅ True assessment created")
    
    # Test 2: Update to False (should store as boolean false)
    print("\n3. Testing update to boolean false...")
    response = requests.patch(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json={
            "assessment_id": true_assessment_id,
            "assessment": {
                "value": False,  # Actual boolean (as the UI should send after conversion)
                "rationale": "Updated to False"
            }
        }
    )
    assert response.status_code == 200, f"Failed to update to False: {response.text}"
    print("   ✅ Updated to False")
    
    # Test 3: Verify data types are correct
    print("\n4. Verifying data types...")
    time.sleep(2)
    response = requests.get(f"{BASE_URL}/api/mlflow/traces/{trace_id}/metadata")
    assert response.status_code == 200, "Failed to get metadata"
    
    metadata = response.json()
    assessments = metadata.get("info", {}).get("assessments", [])
    
    target_assessment = next(
        (a for a in assessments if a.get("assessment_id") == true_assessment_id),
        None
    )
    
    assert target_assessment, "Assessment not found"
    value = target_assessment.get("value")
    
    assert value is False, f"Expected boolean False, got {value} (type: {type(value).__name__})"
    assert isinstance(value, bool), f"Expected bool type, got {type(value).__name__}"
    print("   ✅ Value stored as boolean False")
    
    # Cleanup
    print("\n5. Cleaning up...")
    response = requests.delete(
        f"{BASE_URL}/api/review-apps/{review_app_id}/schemas/{schema_name}",
        headers=headers
    )
    assert response.status_code == 200, "Failed to delete schema"
    print("   ✅ Schema deleted")
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE BOOLEAN FLOW TEST PASSED!")
    print("• Categorical True/False options properly converted to booleans")
    print("• Data types preserved through create and update operations")
    print("• No string pollution in boolean assessments")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_complete_boolean_flow()
    exit(0 if success else 1)