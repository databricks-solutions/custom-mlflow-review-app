#!/usr/bin/env python3
"""Test that we're storing string values "True"/"False" not boolean values."""

import requests


def test_categorical_values():
  """Test that categorical True/False values are stored as strings."""
  base_url = 'http://localhost:8000'
  trace_id = 'tr-0de73a5cfc4e63469900392a8242824f'

  print('Testing categorical value handling...')

  # Step 1: Log feedback with string "True" value
  print("\n1. Logging feedback with string 'True' value...")
  payload = {
    'assessment': {
      'name': 'test_categorical',
      'value': 'True',  # String value, not boolean
      'rationale': 'Testing categorical value',
    }
  }

  response = requests.post(
    f'{base_url}/api/mlflow/traces/{trace_id}/feedback',
    json=payload,
    headers={'Content-Type': 'application/json'},
  )

  if response.status_code == 200:
    result = response.json()
    print(f"   ✅ Logged successfully: {result.get('assessment_id')}")
  else:
    print(f'   ❌ Failed to log: {response.status_code} - {response.text}')
    return

  # Step 2: Retrieve and check the value
  print('\n2. Retrieving trace to check assessment value...')
  response = requests.get(f'{base_url}/api/mlflow/traces/{trace_id}')

  if response.status_code == 200:
    trace_data = response.json()
    assessments = trace_data.get('info', {}).get('assessments', [])

    for assessment in assessments:
      if assessment.get('name') == 'test_categorical':
        value = assessment.get('value')
        print(f'   Assessment value: {repr(value)}')
        print(f'   Type: {type(value)}')
        if value == 'True':
          print("   ✅ PASS: Value is string 'True'")
        elif value is True:
          print('   ⚠️ Value was converted to boolean True')
        else:
          print(f'   ❌ Unexpected value: {value}')
        break
  else:
    print(f'   ❌ Failed to get trace: {response.status_code}')


if __name__ == '__main__':
  test_categorical_values()
