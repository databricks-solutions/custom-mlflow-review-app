#!/usr/bin/env python
"""Simple dtype test for the integration test.
Tests basic boolean and numeric types using a fresh trace.
"""

import time

import requests

BASE_URL = 'http://localhost:8000'


def test_simple_dtypes():
  print('\n' + '=' * 60)
  print('SIMPLE DATA TYPE TEST')
  print('=' * 60)

  # Use a different trace to avoid the 50 assessment limit
  trace_id = 'tr-1ed78f642746008d3e663470b08ef47c'
  print(f'\nUsing trace: {trace_id}')

  # Test 1: Boolean values
  print('\n1. Testing boolean values...')

  # Test True
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={
      'assessment': {'name': 'test_bool_true', 'value': True, 'rationale': 'Testing True boolean'}
    },
  )

  if response.status_code == 200:
    print('   ✅ Boolean True logged successfully')
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Test False
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={
      'assessment': {
        'name': 'test_bool_false',
        'value': False,
        'rationale': 'Testing False boolean',
      }
    },
  )

  if response.status_code == 200:
    print('   ✅ Boolean False logged successfully')
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Test 2: Numeric values
  print('\n2. Testing numeric values...')

  # Integer
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={'assessment': {'name': 'test_integer', 'value': 42, 'rationale': 'Testing integer'}},
  )

  if response.status_code == 200:
    print('   ✅ Integer 42 logged successfully')
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Float
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={'assessment': {'name': 'test_float', 'value': 3.14159, 'rationale': 'Testing float'}},
  )

  if response.status_code == 200:
    print('   ✅ Float 3.14159 logged successfully')
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Test 3: String values (including special cases)
  print('\n3. Testing string values...')

  # Regular string
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={
      'assessment': {'name': 'test_string', 'value': 'Hello World', 'rationale': 'Testing string'}
    },
  )

  if response.status_code == 200:
    print('   ✅ String logged successfully')
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Categorical True/False (string, not boolean)
  response = requests.post(
    f'{BASE_URL}/api/mlflow/traces/{trace_id}/feedback',
    json={
      'assessment': {
        'name': 'test_categorical_true',
        'value': 'True',  # String, not boolean
        'rationale': 'Testing categorical True option',
      }
    },
  )

  if response.status_code == 200:
    print("   ✅ Categorical 'True' string logged successfully")
  else:
    print(f'   ❌ Failed: {response.text}')
    return False

  # Test 4: Verify data types are preserved
  print('\n4. Verifying data types...')

  time.sleep(2)  # Wait for data to propagate

  response = requests.get(f'{BASE_URL}/api/mlflow/traces/{trace_id}/metadata')

  if response.status_code != 200:
    print(f'   ❌ Failed to get metadata: {response.text}')
    return False

  metadata = response.json()
  assessments = metadata.get('info', {}).get('assessments', [])

  # Check boolean True
  bool_true = next((a for a in assessments if a.get('name') == 'test_bool_true'), None)
  if bool_true and bool_true.get('value') is True and isinstance(bool_true.get('value'), bool):
    print('   ✅ Boolean True preserved correctly')
  else:
    print(f'   ❌ Boolean True not preserved: {bool_true}')

  # Check boolean False
  bool_false = next((a for a in assessments if a.get('name') == 'test_bool_false'), None)
  if bool_false and bool_false.get('value') is False and isinstance(bool_false.get('value'), bool):
    print('   ✅ Boolean False preserved correctly')
  else:
    print(f'   ❌ Boolean False not preserved: {bool_false}')

  # Check integer (may be stored as float)
  test_int = next((a for a in assessments if a.get('name') == 'test_integer'), None)
  if test_int and isinstance(test_int.get('value'), (int, float)):
    print(f"   ✅ Integer preserved as numeric: {test_int.get('value')}")
  else:
    print(f'   ❌ Integer not preserved: {test_int}')

  # Check float
  test_float = next((a for a in assessments if a.get('name') == 'test_float'), None)
  if test_float and isinstance(test_float.get('value'), (int, float)):
    print(f"   ✅ Float preserved as numeric: {test_float.get('value')}")
  else:
    print(f'   ❌ Float not preserved: {test_float}')

  # Check string
  test_string = next((a for a in assessments if a.get('name') == 'test_string'), None)
  if test_string and isinstance(test_string.get('value'), str):
    print('   ✅ String preserved correctly')
  else:
    print(f'   ❌ String not preserved: {test_string}')

  # Check categorical True (should be string, not boolean)
  cat_true = next((a for a in assessments if a.get('name') == 'test_categorical_true'), None)
  if cat_true and cat_true.get('value') == 'True' and isinstance(cat_true.get('value'), str):
    print("   ✅ Categorical 'True' preserved as string")
  else:
    print(f"   ❌ Categorical 'True' not preserved: {cat_true}")

  print('\n' + '=' * 60)
  print('✅ DATA TYPE TEST COMPLETED')
  print('=' * 60)

  return True


if __name__ == '__main__':
  # Check server is running
  try:
    response = requests.get(f'{BASE_URL}/health', timeout=2)
    if response.status_code != 200:
      print('❌ Server not healthy')
      exit(1)
  except Exception as e:
    print(f'❌ Server not running: {e}')
    exit(1)

  # Run test
  success = test_simple_dtypes()
  exit(0 if success else 1)
