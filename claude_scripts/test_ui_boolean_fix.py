#!/usr/bin/env python
"""Test the UI boolean fix by simulating the exact request that was failing."""

import requests

BASE_URL = 'http://localhost:8000'


def test_ui_boolean_fix():
  print('Testing UI boolean fix...')

  # Simulate the exact PATCH request that was sending string "False"
  trace_id = 'tr-0de73a5cfc4e63469900392a8242824f'
  assessment_id = 'a-5124ff2291554537a57ceed53e81bbef'

  print(f'Updating assessment {assessment_id} with boolean False...')

  # This should now send actual boolean false, not string "False"
  response = requests.patch(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={
      'assessment_id': assessment_id,
      'assessment': {
        'value': False,  # Actual boolean
        'rationale': 'Testing boolean False conversion.',
      },
    },
  )

  if response.status_code == 200:
    print('✅ Update successful')
  else:
    print(f'❌ Update failed: {response.status_code} - {response.text}')
    return False

  # Verify the value is stored as boolean
  import time

  time.sleep(2)

  response = requests.get(f'{BASE_URL}/api/mlflow/traces/{trace_id}/metadata')
  if response.status_code == 200:
    metadata = response.json()
    assessments = metadata.get('info', {}).get('assessments', [])

    target_assessment = next(
      (a for a in assessments if a.get('assessment_id') == assessment_id), None
    )

    if target_assessment:
      value = target_assessment.get('value')
      if value is False and isinstance(value, bool):
        print('✅ Value correctly stored as boolean False')
        return True
      else:
        print(f'❌ Value not stored correctly: {value} (type: {type(value).__name__})')
        return False
    else:
      print('❌ Assessment not found')
      return False
  else:
    print(f'❌ Failed to get metadata: {response.status_code}')
    return False


if __name__ == '__main__':
  success = test_ui_boolean_fix()
  exit(0 if success else 1)
