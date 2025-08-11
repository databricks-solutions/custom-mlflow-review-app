#!/usr/bin/env python3
"""Test script to verify MLflow assessment update functionality.
Tests: log_assessment -> update_assessment -> verify update
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')


def test_assessment_update():
  """Test the assessment update flow using REST API."""
  # Test configuration
  trace_id = 'tr-3323be404e0e74fc56a4c18e401d5ed0'
  assessment_name = 'test_assessment_script'
  initial_value = 'Initial Value'
  updated_value = 'Updated Value'

  # Get auth from environment
  host = os.getenv('DATABRICKS_HOST')
  token = os.getenv('DATABRICKS_TOKEN')

  if not host or not token:
    print('ERROR: DATABRICKS_HOST and DATABRICKS_TOKEN must be set')
    return False

  headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

  base_url = f'{host}/api/2.0/mlflow'

  print(f"\n{'='*60}")
  print('Testing Assessment Update Flow')
  print(f"{'='*60}")
  print(f'Trace ID: {trace_id}')
  print(f'Timestamp: {datetime.now().isoformat()}')

  # Step 1: Log initial assessment using feedback endpoint
  print('\n1. Creating initial assessment...')
  print(f'   Name: {assessment_name}')
  print(f'   Value: {initial_value}')

  try:
    # Log the initial assessment via REST API
    response = requests.post(
      f'{base_url}/trace/{trace_id}/log-feedback',
      headers=headers,
      json={'key': assessment_name, 'value': initial_value, 'comment': 'Initial test assessment'},
    )

    if response.status_code == 200:
      result = response.json()
      print('   ✓ Assessment created successfully')
      print(f'   Response: {json.dumps(result, indent=2)}')

      # Extract assessment_id from response
      assessment_id = result.get('assessment_id')
      if not assessment_id:
        print('   ✗ No assessment_id in response!')
        return False
      print(f'   Assessment ID: {assessment_id}')
    else:
      print(f'   ✗ Failed to create assessment: {response.status_code}')
      print(f'   Response: {response.text}')
      return False

  except Exception as e:
    print(f'   ✗ Failed to create assessment: {e}')
    return False

  # Step 2: Update the assessment
  print('\n2. Updating assessment...')
  print(f'   Assessment ID: {assessment_id}')
  print(f'   New Value: {updated_value}')

  try:
    # Update the assessment via REST API
    response = requests.post(
      f'{base_url}/trace/{trace_id}/update-feedback',
      headers=headers,
      json={
        'assessment_id': assessment_id,
        'value': updated_value,
        'comment': 'Updated test assessment',
      },
    )

    if response.status_code == 200:
      result = response.json()
      print('   ✓ Assessment updated successfully')
      print(f'   Response: {json.dumps(result, indent=2)}')
    else:
      print(f'   ✗ Failed to update assessment: {response.status_code}')
      print(f'   Response: {response.text}')
      return False

  except Exception as e:
    print(f'   ✗ Failed to update assessment: {e}')
    return False

  # Step 3: Get the trace and verify update
  print('\n3. Verifying update...')

  try:
    # Get the trace via REST API
    response = requests.get(
      f'{base_url}/traces/get-by-request-id', headers=headers, params={'request_id': trace_id}
    )

    if response.status_code == 200:
      trace = response.json()

      # Find our assessment
      assessments = trace.get('assessments', [])
      found_assessment = None

      for assessment in assessments:
        if assessment.get('assessment_id') == assessment_id:
          found_assessment = assessment
          break

      if found_assessment:
        print(f'   ✓ Assessment found with ID: {assessment_id}')

        # Check the value
        actual_value = found_assessment.get('value')
        if not actual_value and 'feedback' in found_assessment:
          actual_value = found_assessment['feedback'].get('value')

        print(f'   Current value: {actual_value}')

        if actual_value == updated_value:
          print('   ✓ SUCCESS: Value was updated correctly!')
          print(f'     Expected: {updated_value}')
          print(f'     Actual: {actual_value}')
          return True
        else:
          print('   ✗ FAILURE: Value was NOT updated!')
          print(f'     Expected: {updated_value}')
          print(f'     Actual: {actual_value}')
          return False
      else:
        print(f'   ✗ Assessment with ID {assessment_id} not found in trace')

        # Show all assessments for debugging
        print('\n   All assessments in trace:')
        for idx, assessment in enumerate(assessments, 1):
          aid = assessment.get('assessment_id', 'N/A')
          name = assessment.get('name', assessment.get('key', 'N/A'))
          value = assessment.get('value')
          if not value and 'feedback' in assessment:
            value = assessment['feedback'].get('value')
          print(f'     [{idx}] ID: {aid}, Name: {name}, Value: {value}')

        return False
    else:
      print(f'   ✗ Failed to get trace: {response.status_code}')
      print(f'   Response: {response.text}')
      return False

  except Exception as e:
    print(f'   ✗ Failed to verify: {e}')
    return False

  print(f"\n{'='*60}\n")


if __name__ == '__main__':
  success = test_assessment_update()
  exit(0 if success else 1)
