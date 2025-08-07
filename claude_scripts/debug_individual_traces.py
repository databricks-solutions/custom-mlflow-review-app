#!/usr/bin/env python3
"""Debug script to investigate individual trace fetching issues."""

import asyncio
import json
import time

import httpx


async def debug_individual_trace_fetching():
  """Debug why individual trace requests are failing."""
  base_url = 'http://localhost:8000'
  experiment_id = '2178582188830602'

  print('🔍 Step 1: Get trace IDs from search')

  async with httpx.AsyncClient(timeout=60.0) as client:
    # First, get some trace IDs from search
    search_response = await client.post(
      f'{base_url}/api/mlflow/search-traces',
      json={'experiment_ids': [experiment_id], 'max_results': 5, 'include_spans': False},
    )

    if search_response.status_code != 200:
      print(f'❌ Search failed: {search_response.status_code}')
      print(f'Response: {search_response.text}')
      return

    search_data = search_response.json()
    traces = search_data.get('traces', [])

    print(f'✅ Search returned {len(traces)} traces')

    if not traces:
      print('❌ No traces found in search results')
      return

    # Extract trace IDs
    trace_ids = []
    for trace in traces:
      trace_id = trace.get('info', {}).get('trace_id')
      if trace_id:
        trace_ids.append(trace_id)
        print(f'   📝 Found trace ID: {trace_id}')

    if not trace_ids:
      print('❌ No trace IDs found in search results')
      return

    print('\n🧪 Step 2: Test individual trace fetching')

    # Test fetching each trace individually
    for i, trace_id in enumerate(trace_ids[:3]):  # Test first 3
      print(f'\n🔍 Testing trace {i + 1}: {trace_id}')

      start_time = time.time()

      try:
        trace_response = await client.get(
          f'{base_url}/api/mlflow/traces/{trace_id}',
          timeout=30.0,  # 30 second timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f'   ⏱️  Response time: {duration * 1000:.1f}ms')
        print(f'   📊 Status code: {trace_response.status_code}')
        print(f'   📦 Response size: {len(trace_response.content)} bytes')

        if trace_response.status_code == 200:
          try:
            trace_data = trace_response.json()
            print('   ✅ SUCCESS: Got trace data')

            # Show trace structure
            if 'info' in trace_data:
              info = trace_data['info']
              print(f'      🆔 Trace ID: {info.get("trace_id", "N/A")}')
              print(f'      📅 Request time: {info.get("request_time", "N/A")}')
              print(f'      🚀 State: {info.get("state", "N/A")}')

            if 'data' in trace_data:
              spans = trace_data['data'].get('spans', [])
              print(f'      🔍 Spans: {len(spans)} spans')

          except json.JSONDecodeError as e:
            print(f'   ⚠️  JSON decode error: {e}')
            print(f'   📄 Raw response: {trace_response.text[:200]}...')

        elif trace_response.status_code == 404:
          print(f'   ❌ NOT FOUND: Trace {trace_id} does not exist')
          print(f'   📄 Response: {trace_response.text}')

          # This is the key issue - why are traces from search not found individually?
          print('   🔍 ANALYSIS: Trace found in search but not in individual fetch!')

        else:
          print(f'   ❌ ERROR: {trace_response.status_code}')
          print(f'   📄 Response: {trace_response.text[:200]}...')

      except asyncio.TimeoutError:
        end_time = time.time()
        duration = end_time - start_time
        print(f'   ⏱️  TIMEOUT after {duration * 1000:.1f}ms')

      except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f'   💥 EXCEPTION after {duration * 1000:.1f}ms: {str(e)}')

    print('\n🔍 Step 3: Compare search vs individual data')

    # Let's examine the search results more closely
    first_trace = traces[0] if traces else None
    if first_trace:
      print('\n📋 First trace from search results:')
      trace_info = first_trace.get('info', {})
      print(f'   🆔 Trace ID: {trace_info.get("trace_id")}')
      print(f'   🧪 Experiment ID: {trace_info.get("trace_location", {}).get("experiment_id")}')
      print(f'   🏃 Run ID: {trace_info.get("trace_location", {}).get("run_id")}')
      print(f'   📅 Request time: {trace_info.get("request_time")}')
      print(f'   🚀 State: {trace_info.get("state")}')

      # Check if there are any obvious issues with the trace ID format
      trace_id = trace_info.get('trace_id', '')
      print('\n🔍 Trace ID analysis:')
      print(f'   📏 Length: {len(trace_id)} characters')
      print(f'   🏷️  Prefix: {trace_id[:5] if len(trace_id) >= 5 else trace_id}')
      format_status = 'Valid' if trace_id.startswith('tr-') and len(trace_id) > 10 else 'Invalid'
      print(f'   🔤 Format: {format_status}')

    print('\n🧪 Step 4: Test trace endpoints directly')

    # Test different trace endpoints to see what works
    if trace_ids:
      test_trace_id = trace_ids[0]

      endpoints_to_test = [
        f'/api/mlflow/traces/{test_trace_id}',
        f'/api/mlflow/traces/{test_trace_id}/data',
        f'/api/mlflow/traces/{test_trace_id}/metadata',
      ]

      for endpoint in endpoints_to_test:
        print(f'\n🔍 Testing endpoint: {endpoint}')

        start_time = time.time()
        try:
          response = await client.get(f'{base_url}{endpoint}', timeout=30.0)
          end_time = time.time()
          duration = end_time - start_time

          print(f'   ⏱️  {duration * 1000:.1f}ms - Status: {response.status_code}')

          if response.status_code == 200:
            print(f'   ✅ SUCCESS - Size: {len(response.content)} bytes')
          else:
            print(f'   ❌ FAILED - Response: {response.text[:100]}...')

        except Exception as e:
          end_time = time.time()
          duration = end_time - start_time
          print(f'   💥 EXCEPTION after {duration * 1000:.1f}ms: {str(e)}')


if __name__ == '__main__':
  asyncio.run(debug_individual_trace_fetching())
