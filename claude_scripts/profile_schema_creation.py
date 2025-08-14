#!/usr/bin/env python
"""Profile label schema creation to identify performance bottlenecks."""

import cProfile
import pstats
import time
from io import StringIO

import httpx


def profile_schema_creation():
  """Profile the schema creation endpoint."""
  base_url = 'http://localhost:8000'

  # Test schema data
  schema_data = {
    'name': f'perf_test_schema_{int(time.time())}',
    'display_name': 'Performance Test Schema',
    'description': 'Schema for performance testing',
    'fields': [
      {
        'name': 'quality',
        'display_name': 'Quality Rating',
        'type': 'rating',
        'config': {'min': 1, 'max': 5},
      },
      {
        'name': 'category',
        'display_name': 'Category',
        'type': 'select',
        'config': {'options': ['good', 'bad', 'neutral']},
      },
    ],
  }

  print('\n🔬 Profiling Schema Creation Performance')
  print('=' * 60)

  # Run with profiling
  profiler = cProfile.Profile()

  print('\n📊 Creating schema with profiling enabled...')
  start_time = time.time()

  profiler.enable()
  response = httpx.post(
    f'{base_url}/api/review-apps/current/label-schemas', json=schema_data, timeout=30.0
  )
  profiler.disable()

  elapsed = (time.time() - start_time) * 1000

  # Report results
  if response.status_code == 200:
    print(f'✅ Schema created successfully in {elapsed:.1f}ms')
    schema = response.json()
    print(f"   Schema ID: {schema['label_schema_id']}")
  else:
    print(f'❌ Schema creation failed: {response.status_code}')
    print(f'   Error: {response.text}')

  # Print profiling stats
  print('\n📈 Top 20 Time-Consuming Operations:')
  print('-' * 60)

  s = StringIO()
  ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
  ps.print_stats(20)

  # Parse and display key insights
  profile_output = s.getvalue()
  print(profile_output)

  # Analyze MLflow/Databricks calls
  print('\n🎯 Key Performance Insights:')
  print('-' * 60)

  s = StringIO()
  ps = pstats.Stats(profiler, stream=s)
  ps.print_callers('fetch_databricks')
  databricks_calls = s.getvalue()

  if 'fetch_databricks' in databricks_calls:
    print('• Databricks API calls detected:')
    print(databricks_calls)
  else:
    print('• No direct Databricks API calls in profile')

  # Check for credential caching
  s = StringIO()
  ps = pstats.Stats(profiler, stream=s)
  ps.print_callers('get_cached_databricks_creds')
  creds_calls = s.getvalue()

  if 'get_cached_databricks_creds' in creds_calls:
    print('\n• Credential caching status:')
    print(creds_calls)

  print('\n✅ Profiling complete!')
  print('\nOptimizations in place:')
  print('• Databricks credentials cached with @lru_cache')
  print('• Workspace info cached with @lru_cache')
  print('• Manifest endpoint uses parallel async execution')
  print('• Per-email user caching available')


if __name__ == '__main__':
  profile_schema_creation()
