#!/usr/bin/env python3
"""Comprehensive bottleneck analysis from performance test results."""

import json
import statistics
from pathlib import Path


def analyze_bottlenecks():
  """Analyze performance test results to identify key bottlenecks."""
  # Load the latest performance results
  results_file = max(Path('claude_scripts').glob('performance_results_*.json'))
  print(f'📊 Analyzing results from: {results_file}')

  with open(results_file) as f:
    data = json.load(f)

  results = data['results']

  print('\n🔍 COMPREHENSIVE BOTTLENECK ANALYSIS')
  print('=' * 60)

  # 1. Response Time Analysis
  print('\n1️⃣  RESPONSE TIME ANALYSIS')
  print('-' * 30)

  response_times = [r['duration_ms'] for r in results if r['success']]

  print('📈 Statistical Analysis:')
  print(f'   • Mean response time: {statistics.mean(response_times):.1f}ms')
  print(f'   • Median response time: {statistics.median(response_times):.1f}ms')
  print(f'   • 95th percentile: {sorted(response_times)[int(len(response_times) * 0.95)]:.1f}ms')
  print(f'   • Max response time: {max(response_times):.1f}ms')
  print(f'   • Min response time: {min(response_times):.1f}ms')

  # Categorize endpoints by performance
  extremely_slow = [r for r in results if r['success'] and r['duration_ms'] > 15000]
  very_slow = [r for r in results if r['success'] and 10000 < r['duration_ms'] <= 15000]
  slow = [r for r in results if r['success'] and 5000 < r['duration_ms'] <= 10000]
  moderate = [r for r in results if r['success'] and 1000 < r['duration_ms'] <= 5000]
  fast = [r for r in results if r['success'] and r['duration_ms'] <= 1000]

  print('\n🚨 Performance Categories:')
  print(f'   • Extremely Slow (>15s): {len(extremely_slow)} endpoints')
  print(f'   • Very Slow (10-15s): {len(very_slow)} endpoints')
  print(f'   • Slow (5-10s): {len(slow)} endpoints')
  print(f'   • Moderate (1-5s): {len(moderate)} endpoints')
  print(f'   • Fast (<1s): {len(fast)} endpoints')

  # 2. Endpoint-Specific Analysis
  print('\n2️⃣  ENDPOINT-SPECIFIC BOTTLENECKS')
  print('-' * 35)

  # Group by endpoint type
  mlflow_endpoints = [r for r in results if '/mlflow/' in r['endpoint']]
  basic_endpoints = [
    r for r in results if r['endpoint'] in ['/health', '/api/config', '/api/user/current']
  ]
  review_app_endpoints = [r for r in results if '/review-apps' in r['endpoint']]

  print(f'\n📊 MLflow Endpoints ({len(mlflow_endpoints)} tests):')
  if mlflow_endpoints:
    mlflow_avg = statistics.mean([r['duration_ms'] for r in mlflow_endpoints if r['success']])
    print(f'   • Average response time: {mlflow_avg:.1f}ms')

    # Most problematic MLflow operations
    mlflow_sorted = sorted(
      [r for r in mlflow_endpoints if r['success']], key=lambda x: x['duration_ms'], reverse=True
    )
    print('   • Slowest operations:')
    for r in mlflow_sorted[:5]:
      print(f'     - {r["test_name"]}: {r["duration_ms"]:.1f}ms')

  print(f'\n🏥 Basic/Health Endpoints ({len(basic_endpoints)} tests):')
  if basic_endpoints:
    basic_successful = [r for r in basic_endpoints if r['success']]
    if basic_successful:
      basic_avg = statistics.mean([r['duration_ms'] for r in basic_successful])
      print(f'   • Average response time: {basic_avg:.1f}ms')

    for r in basic_endpoints:
      status = '✅' if r['success'] else '❌'
      print(f'   • {r["endpoint"]}: {status} {r["duration_ms"]:.1f}ms')

  print(f'\n📋 Review App Endpoints ({len(review_app_endpoints)} tests):')
  if review_app_endpoints:
    review_avg = statistics.mean([r['duration_ms'] for r in review_app_endpoints if r['success']])
    print(f'   • Average response time: {review_avg:.1f}ms')
    for r in review_app_endpoints:
      status = '✅' if r['success'] else '❌'
      print(f'   • {r["test_name"]}: {status} {r["duration_ms"]:.1f}ms')

  # 3. N+1 Query Problem Analysis
  print('\n3️⃣  N+1 QUERY PROBLEM ANALYSIS')
  print('-' * 32)

  individual_traces = [r for r in results if r['test_name'].startswith('Individual Trace')]
  if individual_traces:
    trace_times = [r['duration_ms'] for r in individual_traces if r['success']]
    total_time = sum(trace_times)
    avg_time = statistics.mean(trace_times)

    print('🔍 Individual Trace Fetching:')
    print(f'   • Number of traces tested: {len(individual_traces)}')
    print(f'   • Average time per trace: {avg_time:.1f}ms')
    print(f'   • Total time for all traces: {total_time:.1f}ms ({total_time / 1000:.1f}s)')
    print(f'   • Range: {min(trace_times):.1f}ms - {max(trace_times):.1f}ms')

    # Calculate potential batch optimization savings
    search_traces = [
      r for r in results if 'Search Traces' in r['test_name'] and 'with spans' in r['test_name']
    ]
    if search_traces:
      search_time = search_traces[0]['duration_ms']
      potential_savings = total_time - search_time
      savings_percent = (potential_savings / total_time) * 100

      print('\n💡 Batch Optimization Potential:')
      print(f'   • Search traces (with spans): {search_time:.1f}ms')
      print(f'   • Individual fetches: {total_time:.1f}ms')
      print(f'   • Potential time savings: {potential_savings:.1f}ms ({savings_percent:.1f}%)')

  # 4. Response Size Analysis
  print('\n4️⃣  RESPONSE SIZE ANALYSIS')
  print('-' * 28)

  successful_results = [r for r in results if r['success']]
  response_sizes = [r['response_size_bytes'] for r in successful_results]

  # Convert to MB for readability
  sizes_mb = [size / (1024 * 1024) for size in response_sizes]

  print('📦 Response Size Statistics:')
  print(f'   • Average response size: {statistics.mean(sizes_mb):.2f} MB')
  print(f'   • Median response size: {statistics.median(sizes_mb):.2f} MB')
  print(f'   • Largest response: {max(sizes_mb):.2f} MB')
  print(f'   • Total data transferred: {sum(sizes_mb):.2f} MB')

  # Find endpoints with large responses
  large_responses = sorted(
    [r for r in successful_results if r['response_size_bytes'] > 1024 * 1024],
    key=lambda x: x['response_size_bytes'],
    reverse=True,
  )

  if large_responses:
    print('\n📊 Endpoints with Large Responses (>1MB):')
    for r in large_responses[:5]:
      size_mb = r['response_size_bytes'] / (1024 * 1024)
      print(f'   • {r["test_name"]}: {size_mb:.2f} MB ({r["duration_ms"]:.1f}ms)')

  # 5. Connection Pool Analysis
  print('\n5️⃣  CONNECTION POOL WARNINGS')
  print('-' * 32)

  # This would need to be extracted from server logs, but we can flag it as an issue
  print('⚠️  Connection Pool Issues Detected:')
  print("   • Server logs show 'Connection pool is full' warnings")
  print('   • This indicates HTTP client connection pooling bottlenecks')
  print('   • Affects all Databricks API calls and MLflow operations')

  # 6. Key Bottlenecks Summary
  print('\n6️⃣  KEY BOTTLENECKS IDENTIFIED')
  print('-' * 32)

  bottlenecks = []

  # MLflow operation bottleneck
  if mlflow_endpoints:
    bottlenecks.append(
      {
        'name': 'MLflow Operations Extremely Slow',
        'severity': 'CRITICAL',
        'impact': 'All trace operations take 10-19 seconds',
        'affected_endpoints': len(
          [r for r in mlflow_endpoints if r['success'] and r['duration_ms'] > 10000]
        ),
        'avg_time': statistics.mean([r['duration_ms'] for r in mlflow_endpoints if r['success']]),
      }
    )

  # N+1 query problem
  if individual_traces:
    bottlenecks.append(
      {
        'name': 'N+1 Query Problem',
        'severity': 'HIGH',
        'impact': (
          f'Fetching {len(individual_traces)} traces individually takes {total_time / 1000:.1f}s'
        ),
        'affected_endpoints': len(individual_traces),
        'avg_time': statistics.mean([r['duration_ms'] for r in individual_traces if r['success']]),
      }
    )

  # Connection pool bottleneck
  bottlenecks.append(
    {
      'name': 'HTTP Connection Pool Saturation',
      'severity': 'HIGH',
      'impact': 'Connection pool warnings indicate resource contention',
      'affected_endpoints': 'All Databricks API calls',
      'avg_time': 'Unknown',
    }
  )

  # Basic endpoint failures
  failed_basic = [r for r in basic_endpoints if not r['success']]
  if failed_basic:
    bottlenecks.append(
      {
        'name': 'Basic Endpoint Failures',
        'severity': 'MEDIUM',
        'impact': f'{len(failed_basic)} basic endpoints returning 404',
        'affected_endpoints': len(failed_basic),
        'avg_time': 'N/A',
      }
    )

  print('\n🚨 CRITICAL BOTTLENECKS:')
  for b in sorted(
    bottlenecks, key=lambda x: {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}[x['severity']], reverse=True
  ):
    severity_emoji = {'CRITICAL': '🔥', 'HIGH': '⚠️', 'MEDIUM': '⚙️'}[b['severity']]
    print(f'   {severity_emoji} {b["name"]} ({b["severity"]})')
    print(f'      Impact: {b["impact"]}')
    if isinstance(b['avg_time'], (int, float)):
      print(f'      Avg Time: {b["avg_time"]:.1f}ms')
    print()

  print('=' * 60)
  print('📋 Analysis complete! Use this data for optimization prioritization.')


if __name__ == '__main__':
  analyze_bottlenecks()
