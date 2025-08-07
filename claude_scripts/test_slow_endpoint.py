#!/usr/bin/env python3
"""Test the specific slow endpoint to see detailed timing."""

import logging
import time

import requests

# Configure logging to see all our new traces
logging.basicConfig(
  level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_review_app_endpoint():
  """Test the specific review app endpoint that's hanging."""
  # The endpoint the user mentioned
  url = 'http://localhost:5173/api/review-apps/36cb6150924443a9a8abf3209bcffaf8'

  print('🧪 Testing slow endpoint performance')
  print('=' * 60)
  print(f'URL: {url}')

  try:
    # Make the request with detailed timing
    start_time = time.time()
    print(f"⏰ Starting request at {time.strftime('%H:%M:%S')}")

    response = requests.get(url, timeout=30)

    total_time = time.time() - start_time
    print(f'✅ Request completed in {total_time * 1000:.1f}ms')
    print(f'📊 Status Code: {response.status_code}')
    print(f'📏 Response Size: {len(response.text)} characters')

    # Print response for debugging
    if response.status_code == 200:
      try:
        data = response.json()
        print(f"🔍 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict) and 'review_app_id' in data:
          print(f"📋 Review App ID: {data['review_app_id']}")
          print(f"📋 Experiment ID: {data.get('experiment_id', 'N/A')}")
      except:
        print('⚠️  Response is not valid JSON')
        print(f'📄 Response preview: {response.text[:200]}...')
    else:
      print(f'❌ Error response: {response.text[:500]}')

  except requests.exceptions.Timeout:
    timeout_time = time.time() - start_time
    print(f'⏰ Request TIMED OUT after {timeout_time * 1000:.1f}ms')

  except requests.exceptions.ConnectionError:
    error_time = time.time() - start_time
    print(f'🔌 CONNECTION ERROR after {error_time * 1000:.1f}ms')
    print('❓ Is the development server running on port 5173?')

    # Try the backend directly
    backend_url = url.replace('5173', '8000')
    print(f'🔄 Trying backend directly: {backend_url}')

    try:
      backend_start = time.time()
      backend_response = requests.get(backend_url, timeout=30)
      backend_time = time.time() - backend_start
      print(f'✅ Backend responded in {backend_time * 1000:.1f}ms')
      print(f'📊 Backend Status: {backend_response.status_code}')
    except Exception as e:
      backend_error_time = time.time() - backend_start
      print(f'❌ Backend also failed after {backend_error_time * 1000:.1f}ms: {str(e)}')

  except Exception as e:
    error_time = time.time() - start_time
    print(f'💥 Unexpected error after {error_time * 1000:.1f}ms: {str(e)}')


def test_multiple_endpoints():
  """Test multiple endpoints to compare performance."""
  endpoints = [
    ('http://localhost:8000/health', 'Health check'),
    ('http://localhost:8000/api/config/', 'Config endpoint'),
    (
      'http://localhost:8000/api/review-apps/36cb6150924443a9a8abf3209bcffaf8',
      'Slow review app endpoint',
    ),
  ]

  print('\n🚀 Testing Multiple Endpoints for Comparison')
  print('=' * 60)

  for url, description in endpoints:
    print(f'\n📡 Testing: {description}')
    print(f'   URL: {url}')

    try:
      start = time.time()
      resp = requests.get(url, timeout=15)
      elapsed = time.time() - start

      print(f'   ✅ {elapsed * 1000:>7.1f}ms - Status: {resp.status_code}')

    except requests.exceptions.Timeout:
      elapsed = time.time() - start
      print(f'   ⏰ {elapsed * 1000:>7.1f}ms - TIMEOUT')

    except Exception as e:
      elapsed = time.time() - start
      print(f'   ❌ {elapsed * 1000:>7.1f}ms - ERROR: {str(e)[:50]}')


if __name__ == '__main__':
  test_review_app_endpoint()
  test_multiple_endpoints()

  print('\n💡 Next Steps:')
  print('1. Check the server logs to see our detailed tracing:')
  print('   tail -f /tmp/databricks-app-watch.log')
  print('2. Look for these log patterns:')
  print('   🌐 [DATABRICKS ASYNC/SYNC] - API call timing')
  print('   🧬 [MLFLOW GENAI] - SDK call timing')
  print('   🔍 [MLFLOW SDK] - MLflow operations')
  print('   🔐 [DATABRICKS] - Credential lookup timing')
