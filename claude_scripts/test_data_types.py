#!/usr/bin/env python
"""Test script to verify that boolean and numeric assessment values
are stored with correct data types instead of being stringified.
"""

import time

import requests

# API base URL
BASE_URL = 'http://localhost:8000'


def test_assessment_data_types():
  """Test that assessments are stored with correct data types."""
  print('Testing Assessment Data Types')
  print('=' * 50)

  # First, get a trace to test with
  search_payload = {'experiment_ids': [], 'max_results': 1}

  print('\n1. Searching for a trace...')
  response = requests.post(f'{BASE_URL}/api/mlflow/search-traces', json=search_payload)
  response.raise_for_status()
  traces = response.json().get('traces', [])

  if not traces:
    print('   ❌ No traces found. Please ensure there are traces in the system.')
    return False

  # Extract trace_id - the structure varies based on the API response
  if isinstance(traces[0], dict) and 'info' in traces[0]:
    trace_id = traces[0]['info']['trace_id']
  elif isinstance(traces[0], dict) and 'trace_id' in traces[0]:
    trace_id = traces[0]['trace_id']
  else:
    print(
      f'   ❌ Unexpected trace structure: {traces[0].keys() if isinstance(traces[0], dict) else type(traces[0])}'
    )
    return False
  print(f'   ✓ Found trace: {trace_id}')

  # Test boolean assessment
  print('\n2. Testing boolean assessment...')
  bool_feedback = {
    'assessment': {
      'name': 'test_boolean',
      'value': True,  # Actual boolean, not string "True"
      'rationale': 'Testing boolean data type',
    }
  }

  response = requests.post(f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback', json=bool_feedback)
  if response.status_code != 200:
    print(f'   ❌ Error: {response.status_code} - {response.text}')
    return False
  result = response.json()
  assessment_id_bool = result.get('assessment_id')
  print(f'   ✓ Created boolean assessment: {assessment_id_bool}')

  # Test numeric assessment
  print('\n3. Testing numeric assessment...')
  num_feedback = {
    'assessment': {
      'name': 'test_numeric',
      'value': 4.5,  # Actual number, not string "4.5"
      'rationale': 'Testing numeric data type',
    }
  }

  response = requests.post(f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback', json=num_feedback)
  if response.status_code != 200:
    print(f'   ❌ Error: {response.status_code} - {response.text}')
    return False
  result = response.json()
  assessment_id_num = result.get('assessment_id')
  print(f'   ✓ Created numeric assessment: {assessment_id_num}')

  # Wait a moment for data to propagate
  time.sleep(1)

  # Retrieve the trace to check assessment values
  print('\n4. Retrieving trace to verify data types...')
  response = requests.get(f'{BASE_URL}/api/mlflow/traces/{trace_id}/metadata')
  response.raise_for_status()
  trace_data = response.json()

  assessments = trace_data.get('info', {}).get('assessments', [])

  # Check boolean assessment
  bool_assessment = next((a for a in assessments if a.get('name') == 'test_boolean'), None)

  if bool_assessment:
    value = bool_assessment.get('value')
    value_type = type(value).__name__

    if isinstance(value, bool):
      print('   ✅ Boolean assessment stored correctly')
      print(f'      Value: {value} (type: {value_type})')
    else:
      print('   ❌ Boolean assessment stored as wrong type!')
      print(f'      Value: {value} (type: {value_type})')
      print(f'      Expected type: bool, got: {value_type}')
  else:
    print('   ❌ Boolean assessment not found')

  # Check numeric assessment
  num_assessment = next((a for a in assessments if a.get('name') == 'test_numeric'), None)

  if num_assessment:
    value = num_assessment.get('value')
    value_type = type(value).__name__

    if isinstance(value, (int, float)):
      print('   ✅ Numeric assessment stored correctly')
      print(f'      Value: {value} (type: {value_type})')
    else:
      print('   ❌ Numeric assessment stored as wrong type!')
      print(f'      Value: {value} (type: {value_type})')
      print(f'      Expected type: int/float, got: {value_type}')
  else:
    print('   ❌ Numeric assessment not found')

  print('\n' + '=' * 50)
  print('Test Complete')

  # Return success if both are correct types
  return (
    bool_assessment
    and isinstance(bool_assessment.get('value'), bool)
    and num_assessment
    and isinstance(num_assessment.get('value'), (int, float))
  )


if __name__ == '__main__':
  try:
    success = test_assessment_data_types()
    exit(0 if success else 1)
  except Exception as e:
    print(f'\n❌ Test failed with error: {e}')
    exit(1)
