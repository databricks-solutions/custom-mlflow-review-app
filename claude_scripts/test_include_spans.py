#!/usr/bin/env python3
"""Test to verify include_spans parameter is working correctly."""

import asyncio
import json
import time

import httpx


async def test_include_spans_parameter():
  """Test search-traces with and without spans to measure the difference."""
  base_url = 'http://localhost:8000'
  experiment_id = '2178582188830602'

  test_cases = [
    {
      'name': 'No spans (include_spans=False)',
      'data': {'experiment_ids': [experiment_id], 'max_results': 5, 'include_spans': False},
    },
    {
      'name': 'With spans (include_spans=True)',
      'data': {'experiment_ids': [experiment_id], 'max_results': 5, 'include_spans': True},
    },
    {
      'name': 'Default (no include_spans parameter)',
      'data': {'experiment_ids': [experiment_id], 'max_results': 5},
    },
  ]

  results = []

  async with httpx.AsyncClient(timeout=60.0) as client:
    for test_case in test_cases:
      print(f'\n🧪 Testing: {test_case["name"]}')

      start_time = time.time()

      try:
        response = await client.post(
          f'{base_url}/api/mlflow/search-traces',
          json=test_case['data'],
          headers={'Content-Type': 'application/json'},
        )

        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
          data = response.json()
          traces_count = len(data.get('traces', []))

          # Calculate spans info
          total_spans = 0
          traces_with_spans = 0

          for trace in data.get('traces', []):
            spans = trace.get('data', {}).get('spans', [])
            if spans:
              traces_with_spans += 1
              total_spans += len(spans)

          result = {
            'test': test_case['name'],
            'duration_ms': round(duration * 1000, 1),
            'success': True,
            'status_code': response.status_code,
            'response_size_bytes': len(response.content),
            'traces_count': traces_count,
            'traces_with_spans': traces_with_spans,
            'total_spans': total_spans,
            'avg_spans_per_trace': round(total_spans / traces_count, 1) if traces_count > 0 else 0,
          }

          print(f'✅ SUCCESS: {duration * 1000:.1f}ms')
          print(f'   📊 Response: {len(response.content)} bytes, {traces_count} traces')
          print(f'   🔍 Spans: {total_spans} total spans across {traces_with_spans} traces')

        else:
          result = {
            'test': test_case['name'],
            'duration_ms': round(duration * 1000, 1),
            'success': False,
            'status_code': response.status_code,
            'error': response.text[:200],
            'response_size_bytes': len(response.content),
          }

          print(f'❌ FAILED: {response.status_code} in {duration * 1000:.1f}ms')
          print(f'   Error: {response.text[:100]}')

        results.append(result)

      except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        result = {
          'test': test_case['name'],
          'duration_ms': round(duration * 1000, 1),
          'success': False,
          'exception': str(e),
        }

        print(f'💥 EXCEPTION: {str(e)} after {duration * 1000:.1f}ms')
        results.append(result)

  # Summary
  print('\n📋 SUMMARY')
  print(
    f'{"Test":<40} {"Duration":<12} {"Success":<8} {"Traces":<8} {"Spans":<8} {"Response Size":<15}'
  )
  print('-' * 100)

  for result in results:
    duration_str = f'{result["duration_ms"]:.1f}ms'
    success_str = '✅' if result.get('success') else '❌'
    traces_str = str(result.get('traces_count', 'N/A'))
    spans_str = str(result.get('total_spans', 'N/A'))
    size_str = f'{result.get("response_size_bytes", 0)} B'

    print(
      f'{result["test"]:<40} {duration_str:<12} {success_str:<8} '
      f'{traces_str:<8} {spans_str:<8} {size_str:<15}'
    )

  # Analysis
  print('\n🔍 ANALYSIS')

  success_results = [r for r in results if r.get('success')]
  if len(success_results) >= 2:
    no_spans = next((r for r in success_results if 'No spans' in r['test']), None)
    with_spans = next((r for r in success_results if 'With spans' in r['test']), None)

    if no_spans and with_spans:
      time_diff = with_spans['duration_ms'] - no_spans['duration_ms']
      size_diff = with_spans['response_size_bytes'] - no_spans['response_size_bytes']

      print(
        f'⏱️  Time difference: {time_diff:+.1f}ms '
        f'({time_diff / no_spans["duration_ms"] * 100:+.1f}%)'
      )
      print(
        f'📦 Size difference: {size_diff:+,} bytes '
        f'({size_diff / no_spans["response_size_bytes"] * 100:+.1f}%)'
      )

      if with_spans.get('total_spans', 0) > 0:
        print(
          f'🔍 Spans included: {with_spans["total_spans"]} spans across '
          f'{with_spans["traces_count"]} traces'
        )
        print(f'   Average spans per trace: {with_spans["avg_spans_per_trace"]:.1f}')

      if no_spans.get('total_spans', 0) == 0:
        print('✅ include_spans=False working correctly - no spans in response')
      else:
        print(f'⚠️  include_spans=False may not be working - found {no_spans["total_spans"]} spans')

  # Save results
  with open('claude_scripts/include_spans_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

  print('\n💾 Results saved to: claude_scripts/include_spans_test_results.json')


if __name__ == '__main__':
  asyncio.run(test_include_spans_parameter())
