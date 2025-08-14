#!/usr/bin/env python
"""Test script to measure API endpoint performance with caching improvements."""

import asyncio
import time
from statistics import mean, median, stdev

import httpx


async def test_endpoint(url: str, name: str, iterations: int = 5):
  """Test an endpoint multiple times and report performance."""
  async with httpx.AsyncClient() as client:
    times = []

    print(f"\n{'='*60}")
    print(f'Testing {name}: {url}')
    print(f"{'='*60}")

    for i in range(iterations):
      start = time.time()
      response = await client.get(url)
      elapsed = (time.time() - start) * 1000  # Convert to ms
      times.append(elapsed)

      status = '✅' if response.status_code == 200 else f'❌ {response.status_code}'
      cache_status = '🔥 WARM' if i > 0 else '❄️  COLD'
      print(f'  Run {i+1}: {elapsed:7.1f}ms {status} {cache_status}')

    # Statistics
    print(f'\nStatistics for {name}:')
    print(f'  • First call (cold): {times[0]:.1f}ms')
    if len(times) > 1:
      print(f'  • Subsequent (warm): {mean(times[1:]):.1f}ms avg')
      print(f'  • Speedup: {times[0]/mean(times[1:]):.1f}x')
    print(f'  • Min: {min(times):.1f}ms')
    print(f'  • Max: {max(times):.1f}ms')
    print(f'  • Mean: {mean(times):.1f}ms')
    print(f'  • Median: {median(times):.1f}ms')
    if len(times) > 1:
      print(f'  • Stdev: {stdev(times):.1f}ms')

    return times


async def main():
  """Run performance tests on key endpoints."""
  base_url = 'http://localhost:8000'

  print('\n🚀 API Performance Test Suite')
  print('Testing with caching improvements...')

  # Test endpoints
  endpoints = [
    ('/api/user/me', 'User Info'),
    ('/api/manifest', 'App Manifest'),
    ('/api/config', 'Configuration'),
    ('/api/review-apps/current', 'Current Review App'),
  ]

  all_results = {}
  for endpoint, name in endpoints:
    url = f'{base_url}{endpoint}'
    try:
      times = await test_endpoint(url, name)
      all_results[name] = times
    except Exception as e:
      print(f'\n❌ Error testing {name}: {e}')

  # Summary
  print('\n' + '=' * 60)
  print('PERFORMANCE SUMMARY')
  print('=' * 60)

  for name, times in all_results.items():
    if times:
      improvement = ((times[0] - mean(times[1:])) / times[0] * 100) if len(times) > 1 else 0
      print(
        f'{name:20} | First: {times[0]:6.1f}ms | Avg: {mean(times):6.1f}ms | '
        f'Cache improvement: {improvement:5.1f}%'
      )

  print('\n✅ Performance test complete!')
  print('\nKey observations:')
  print('• Credential caching eliminates auth lookup overhead')
  print('• Workspace info is cached with @lru_cache decorator')
  print('• Manifest endpoint uses parallel async execution')
  print('• Per-email user caching available for multi-user scenarios')


if __name__ == '__main__':
  asyncio.run(main())
