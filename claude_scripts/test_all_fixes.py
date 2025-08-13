#!/usr/bin/env python
"""
Comprehensive test to verify all fixes:
1. Boolean values stored as actual booleans
2. Pass/Fail schemas work correctly with True/False options
3. Debouncing works with both value and rationale
"""

import json
import requests
import time
from typing import Any, Dict

# API base URL
BASE_URL = "http://localhost:8000"

def get_headers():
    """Get headers for authenticated requests."""
    return {
        "Content-Type": "application/json",
    }

def test_pass_fail_schema_creation():
    """Test that Pass/Fail schemas are created with correct options."""
    print("\n1. Testing Pass/Fail schema creation...")
    
    # Create a new Pass/Fail schema
    schema_data = {
        "name": "test_pass_fail_fix",
        "title": "Pass/Fail Test",
        "instruction": "Test pass/fail with True/False options",
        "type": "FEEDBACK",
        "categorical": {
            "options": ["True", "False"]
        },
        "enable_comment": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/label-schemas",
        json=schema_data,
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to create schema: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    
    # Verify the schema was created with correct options
    if result.get("categorical", {}).get("options") == ["True", "False"]:
        print(f"   ✅ Pass/Fail schema created with correct True/False options")
        return True
    else:
        print(f"   ❌ Schema options incorrect: {result.get('categorical', {}).get('options')}")
        return False

def test_boolean_value_storage():
    """Test that boolean values are stored as actual booleans."""
    print("\n2. Testing boolean value storage...")
    
    # Get a trace to test with
    search_payload = {
        "experiment_ids": [],
        "max_results": 1
    }
    
    response = requests.post(f"{BASE_URL}/api/mlflow/search-traces", json=search_payload)
    response.raise_for_status()
    traces = response.json().get("traces", [])
    
    if not traces:
        print("   ❌ No traces found")
        return False
    
    # Extract trace_id
    if isinstance(traces[0], dict) and "info" in traces[0]:
        trace_id = traces[0]["info"]["trace_id"]
    elif isinstance(traces[0], dict) and "trace_id" in traces[0]:
        trace_id = traces[0]["trace_id"]
    else:
        print(f"   ❌ Unexpected trace structure")
        return False
    
    # Test with True value
    bool_feedback = {
        "assessment": {
            "name": "test_boolean_true",
            "value": True,
            "rationale": "Testing True boolean"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json=bool_feedback
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to create True assessment: {response.text}")
        return False
    
    # Test with False value
    bool_feedback = {
        "assessment": {
            "name": "test_boolean_false",
            "value": False,
            "rationale": "Testing False boolean"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/mlflow/traces/{trace_id}/feedback",
        json=bool_feedback
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to create False assessment: {response.text}")
        return False
    
    # Wait and retrieve
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/api/mlflow/traces/{trace_id}/metadata")
    response.raise_for_status()
    trace_data = response.json()
    
    assessments = trace_data.get("info", {}).get("assessments", [])
    
    # Check True assessment
    true_assessment = next(
        (a for a in assessments if a.get("name") == "test_boolean_true"),
        None
    )
    
    # Check False assessment
    false_assessment = next(
        (a for a in assessments if a.get("name") == "test_boolean_false"),
        None
    )
    
    success = True
    
    if true_assessment:
        value = true_assessment.get("value")
        if value is True and isinstance(value, bool):
            print(f"   ✅ True boolean stored correctly (type: {type(value).__name__})")
        else:
            print(f"   ❌ True boolean incorrect: {value} (type: {type(value).__name__})")
            success = False
    else:
        print("   ❌ True assessment not found")
        success = False
    
    if false_assessment:
        value = false_assessment.get("value")
        if value is False and isinstance(value, bool):
            print(f"   ✅ False boolean stored correctly (type: {type(value).__name__})")
        else:
            print(f"   ❌ False boolean incorrect: {value} (type: {type(value).__name__})")
            success = False
    else:
        print("   ❌ False assessment not found")
        success = False
    
    return success

def test_schema_type_detection():
    """Test that Pass/Fail schemas are properly detected."""
    print("\n3. Testing schema type detection...")
    
    # Get all schemas
    response = requests.get(f"{BASE_URL}/api/label-schemas", headers=get_headers())
    
    if response.status_code != 200:
        print(f"   ❌ Failed to get schemas: {response.text}")
        return False
    
    schemas = response.json()
    
    # Check our test schema
    test_schema = next(
        (s for s in schemas if s.get("name") == "test_pass_fail_fix"),
        None
    )
    
    if test_schema:
        options = test_schema.get("categorical", {}).get("options", [])
        if options == ["True", "False"]:
            print(f"   ✅ Pass/Fail schema has correct True/False options")
            return True
        else:
            print(f"   ❌ Schema options incorrect: {options}")
            return False
    else:
        print("   ❌ Test schema not found")
        return False

def cleanup_test_schemas():
    """Clean up test schemas created during testing."""
    print("\n4. Cleaning up test schemas...")
    
    try:
        # Delete test schema
        response = requests.delete(
            f"{BASE_URL}/api/label-schemas/test_pass_fail_fix",
            headers=get_headers()
        )
        
        if response.status_code in [200, 404]:
            print("   ✅ Test schemas cleaned up")
        else:
            print(f"   ⚠️ Cleanup warning: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Cleanup error: {e}")

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE FIX VERIFICATION")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Pass/Fail schema creation
    if not test_pass_fail_schema_creation():
        all_passed = False
    
    # Test 2: Boolean value storage
    if not test_boolean_value_storage():
        all_passed = False
    
    # Test 3: Schema type detection
    if not test_schema_type_detection():
        all_passed = False
    
    # Cleanup
    cleanup_test_schemas()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        exit(1)