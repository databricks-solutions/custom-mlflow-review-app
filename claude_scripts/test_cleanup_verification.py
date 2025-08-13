#!/usr/bin/env python
"""
Test script to verify the cleanup functionality works correctly.
This creates a test schema and session, then cleans them up.
"""

import time
import requests

BASE_URL = "http://localhost:8000"

def test_cleanup():
    print("=" * 60)
    print("CLEANUP FUNCTIONALITY TEST")
    print("=" * 60)
    
    headers = {'Content-Type': 'application/json'}
    timestamp = int(time.time())
    
    # Get review app ID
    print("\n1. Getting review app ID...")
    response = requests.get(f"{BASE_URL}/api/manifest")
    if response.status_code != 200:
        print(f"❌ Failed to get manifest: {response.status_code}")
        return False
    
    manifest = response.json()
    review_app_id = manifest.get('config', {}).get('review_app_id')
    print(f"✅ Review app ID: {review_app_id}")
    
    # Create test schema
    print("\n2. Creating test schema...")
    test_schema = {
        'name': f'cleanup_test_{timestamp}',
        'type': 'FEEDBACK',
        'title': 'Cleanup Test Schema',
        'instruction': 'This is a test schema for cleanup verification',
        'categorical': {'options': ['True', 'False']},
    }
    
    response = requests.post(
        f"{BASE_URL}/api/review-apps/{review_app_id}/schemas",
        json=test_schema,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create schema: {response.status_code} - {response.text}")
        return False
    
    print(f"✅ Created schema: {test_schema['name']}")
    
    # Verify schema exists
    print("\n3. Verifying schema exists...")
    response = requests.get(f"{BASE_URL}/api/review-apps/{review_app_id}/schemas")
    if response.status_code == 200:
        schemas = response.json()
        schema_names = [s.get('name') for s in schemas]
        if test_schema['name'] in schema_names:
            print(f"✅ Schema confirmed in list")
        else:
            print(f"❌ Schema not found in list")
            return False
    
    # Delete the schema
    print("\n4. Deleting test schema...")
    response = requests.delete(
        f"{BASE_URL}/api/review-apps/{review_app_id}/schemas/{test_schema['name']}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to delete schema: {response.status_code} - {response.text}")
        return False
    
    print(f"✅ Schema deleted successfully")
    
    # Verify schema is gone
    print("\n5. Verifying schema is deleted...")
    time.sleep(2)  # Small delay
    
    response = requests.get(f"{BASE_URL}/api/review-apps/{review_app_id}/schemas")
    if response.status_code == 200:
        schemas = response.json()
        schema_names = [s.get('name') for s in schemas]
        if test_schema['name'] not in schema_names:
            print(f"✅ Schema confirmed deleted from list")
        else:
            print(f"❌ Schema still exists in list")
            return False
    
    # Try to get the specific schema (should return 404)
    response = requests.get(
        f"{BASE_URL}/api/review-apps/{review_app_id}/schemas/{test_schema['name']}"
    )
    if response.status_code == 404:
        print(f"✅ Direct schema lookup returns 404 (correctly deleted)")
    else:
        print(f"❌ Schema still accessible: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ CLEANUP FUNCTIONALITY VERIFIED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server not healthy")
            exit(1)
    except Exception as e:
        print(f"❌ Server not running: {e}")
        exit(1)
    
    # Run test
    success = test_cleanup()
    exit(0 if success else 1)