#!/usr/bin/env python3
"""Test script to verify our REST API boolean handling."""

import requests


def test_api_boolean_feedback():
  """Test logging boolean feedback via our REST API."""
  trace_id = 'tr-c9ba18c61e323bb6c7375d11cd297eea'
  base_url = 'http://localhost:8000'

  print('Testing boolean feedback via REST API...')

  try:
    # Test logging True via REST API
    print('\n1. Logging boolean True via REST API...')
    payload = {
      'assessment': {
        'name': 'api_test_boolean_true',
        'value': True,  # Actual boolean
        'rationale': 'Test boolean true via REST',
      }
    }

    response = requests.post(
      f'{base_url}/api/mlflow/traces/{trace_id}/feedback',
      json=payload,
      headers={'Content-Type': 'application/json'},
    )

    if response.status_code == 200:
      result = response.json()
      print(f'   Success: {result}')
    else:
      print(f'   Error: {response.status_code} - {response.text}')
      return

    # Test logging False via REST API
    print('\n2. Logging boolean False via REST API...')
    payload = {
      'assessment': {
        'name': 'api_test_boolean_false',
        'value': False,  # Actual boolean
        'rationale': 'Test boolean false via REST',
      }
    }

    response = requests.post(
      f'{base_url}/api/mlflow/traces/{trace_id}/feedback',
      json=payload,
      headers={'Content-Type': 'application/json'},
    )

    if response.status_code == 200:
      result = response.json()
      print(f'   Success: {result}')
    else:
      print(f'   Error: {response.status_code} - {response.text}')
      return

    # Now retrieve the trace via our REST API to see what we get back
    print('\n3. Retrieving trace via REST API to check values...')
    response = requests.get(f'{base_url}/api/mlflow/traces/{trace_id}')

    if response.status_code == 200:
      trace_data = response.json()
      assessments = trace_data.get('info', {}).get('assessments', [])
      print(f'   Found {len(assessments)} assessments')

      for assessment in assessments:
        name = assessment.get('name', '')
        if name.startswith('api_test_boolean_'):
          value = assessment.get('value')
          print(f"   Assessment '{name}': {value} (type: {type(value)})")
    else:
      print(f'   Error retrieving trace: {response.status_code} - {response.text}')

  except Exception as e:
    print(f'Error: {e}')
    import traceback

    traceback.print_exc()


if __name__ == '__main__':
  test_api_boolean_feedback()
