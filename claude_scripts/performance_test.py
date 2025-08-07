#!/usr/bin/env python3
"""Performance testing script for FastAPI server bottleneck analysis.

This script tests various endpoints in parallel to identify bottlenecks and
measure response times across different scenarios.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


class PerformanceAnalyzer:
  """Analyze FastAPI server performance across multiple endpoints."""

  def __init__(self, base_url: str = 'http://localhost:8000'):
    self.base_url = base_url
    self.console = Console()
    self.results: List[Dict[str, Any]] = []

    # Load config for experiment IDs
    try:
      with open('config.yaml', 'r') as f:
        self.config = yaml.safe_load(f)
      self.experiment_id = self.config['mlflow']['experiment_id']
    except Exception as e:
      self.console.print(f'[red]Warning: Could not load config: {e}[/red]')
      self.experiment_id = '2178582188830602'  # fallback

  async def fetch_endpoint(
    self,
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    test_name: str = '',
  ) -> Dict[str, Any]:
    """Fetch a single endpoint and measure performance."""
    start_time = time.time()

    try:
      response = await client.request(
        method=method, url=f'{self.base_url}{endpoint}', json=data, params=params, timeout=30.0
      )

      end_time = time.time()
      duration_ms = (end_time - start_time) * 1000

      result = {
        'test_name': test_name or f'{method} {endpoint}',
        'method': method,
        'endpoint': endpoint,
        'status_code': response.status_code,
        'duration_ms': round(duration_ms, 2),
        'response_size_bytes': len(response.content),
        'success': response.status_code < 400,
        'timestamp': datetime.now().isoformat(),
      }

      # Add response data size info
      if response.headers.get('content-type', '').startswith('application/json'):
        try:
          json_data = response.json()
          if isinstance(json_data, dict):
            result['response_keys'] = list(json_data.keys())
            if 'traces' in json_data:
              result['traces_count'] = len(json_data['traces'])
            if 'review_apps' in json_data:
              result['review_apps_count'] = len(json_data['review_apps'])
        except (ValueError, KeyError, TypeError):
          pass

      return result

    except Exception as e:
      end_time = time.time()
      duration_ms = (end_time - start_time) * 1000

      return {
        'test_name': test_name or f'{method} {endpoint}',
        'method': method,
        'endpoint': endpoint,
        'status_code': 0,
        'duration_ms': round(duration_ms, 2),
        'response_size_bytes': 0,
        'success': False,
        'error': str(e),
        'timestamp': datetime.now().isoformat(),
      }

  async def test_basic_endpoints(self) -> List[Dict[str, Any]]:
    """Test basic health and config endpoints."""
    async with httpx.AsyncClient() as client:
      tests = [
        ('GET', '/health', None, None, 'Health Check'),
        ('GET', '/api/config', None, None, 'Config Endpoint'),
        ('GET', '/api/user/current', None, None, 'Current User'),
      ]

      tasks = [
        self.fetch_endpoint(client, method, endpoint, data, params, name)
        for method, endpoint, data, params, name in tests
      ]

      return await asyncio.gather(*tasks)

  async def test_mlflow_endpoints(self) -> List[Dict[str, Any]]:
    """Test MLflow proxy endpoints."""
    async with httpx.AsyncClient() as client:
      # Test search traces with different parameters
      search_tests = [
        {
          'endpoint': '/api/mlflow/search-traces',
          'data': {
            'experiment_ids': [self.experiment_id],
            'max_results': 10,
            'include_spans': False,
          },
          'name': 'Search Traces (10, no spans)',
        },
        {
          'endpoint': '/api/mlflow/search-traces',
          'data': {
            'experiment_ids': [self.experiment_id],
            'max_results': 50,
            'include_spans': False,
          },
          'name': 'Search Traces (50, no spans)',
        },
        {
          'endpoint': '/api/mlflow/search-traces',
          'data': {
            'experiment_ids': [self.experiment_id],
            'max_results': 10,
            'include_spans': True,
          },
          'name': 'Search Traces (10, with spans)',
        },
      ]

      tasks = []
      for test in search_tests:
        tasks.append(
          self.fetch_endpoint(client, 'POST', test['endpoint'], test['data'], None, test['name'])
        )

      # Add experiment endpoint test
      tasks.append(
        self.fetch_endpoint(
          client,
          'GET',
          f'/api/mlflow/experiments/{self.experiment_id}',
          None,
          None,
          'Get Experiment',
        )
      )

      return await asyncio.gather(*tasks)

  async def test_review_app_endpoints(self) -> List[Dict[str, Any]]:
    """Test review app endpoints."""
    async with httpx.AsyncClient() as client:
      tests = [
        {
          'endpoint': '/api/review-apps',
          'params': {'filter': f'experiment_id={self.experiment_id}'},
          'name': 'List Review Apps',
        },
      ]

      tasks = []
      for test in tests:
        tasks.append(
          self.fetch_endpoint(
            client, 'GET', test['endpoint'], None, test.get('params'), test['name']
          )
        )

      return await asyncio.gather(*tasks)

  async def test_parallel_trace_fetching(self, trace_ids: List[str]) -> List[Dict[str, Any]]:
    """Test fetching multiple traces in parallel (simulates N+1 problem)."""
    if not trace_ids:
      self.console.print('[yellow]No trace IDs available for parallel testing[/yellow]')
      return []

    async with httpx.AsyncClient() as client:
      # Test individual trace requests (current approach)
      tasks = []
      for i, trace_id in enumerate(trace_ids[:10]):  # Limit to 10 traces
        tasks.append(
          self.fetch_endpoint(
            client, 'GET', f'/api/mlflow/traces/{trace_id}', None, None, f'Individual Trace {i + 1}'
          )
        )

      return await asyncio.gather(*tasks)

  async def get_sample_trace_ids(self) -> List[str]:
    """Get some trace IDs for testing individual trace fetching."""
    async with httpx.AsyncClient() as client:
      try:
        response = await client.post(
          f'{self.base_url}/api/mlflow/search-traces',
          json={'experiment_ids': [self.experiment_id], 'max_results': 20, 'include_spans': False},
          timeout=30.0,
        )

        if response.status_code == 200:
          data = response.json()
          traces = data.get('traces', [])
          return [
            trace['info']['trace_id']
            for trace in traces
            if 'info' in trace and 'trace_id' in trace['info']
          ]

      except Exception as e:
        self.console.print(f'[red]Could not get trace IDs: {e}[/red]')

    return []

  async def run_comprehensive_test(self) -> None:
    """Run all performance tests and analyze results."""
    self.console.print('[bold blue]🚀 Starting Comprehensive Performance Analysis[/bold blue]')

    with Progress(
      SpinnerColumn(), TextColumn('[progress.description]{task.description}'), console=self.console
    ) as progress:
      # Test 1: Basic endpoints
      task1 = progress.add_task('Testing basic endpoints...', total=1)
      basic_results = await self.test_basic_endpoints()
      self.results.extend(basic_results)
      progress.advance(task1)

      # Test 2: MLflow endpoints
      task2 = progress.add_task('Testing MLflow endpoints...', total=1)
      mlflow_results = await self.test_mlflow_endpoints()
      self.results.extend(mlflow_results)
      progress.advance(task2)

      # Test 3: Review app endpoints
      task3 = progress.add_task('Testing review app endpoints...', total=1)
      review_results = await self.test_review_app_endpoints()
      self.results.extend(review_results)
      progress.advance(task3)

      # Test 4: Get sample trace IDs
      task4 = progress.add_task('Getting sample trace IDs...', total=1)
      trace_ids = await self.get_sample_trace_ids()
      progress.advance(task4)

      # Test 5: Parallel trace fetching (N+1 problem simulation)
      if trace_ids:
        task5 = progress.add_task(
          f'Testing parallel trace fetching ({len(trace_ids[:10])} traces)...', total=1
        )
        parallel_results = await self.test_parallel_trace_fetching(trace_ids)
        self.results.extend(parallel_results)
        progress.advance(task5)

    # Analyze and display results
    self.analyze_results()
    self.save_results()

  def analyze_results(self) -> None:
    """Analyze test results and display performance insights."""
    if not self.results:
      self.console.print('[red]No results to analyze[/red]')
      return

    self.console.print('\n[bold green]📊 Performance Analysis Results[/bold green]')

    # Create summary table
    table = Table(title='Endpoint Performance Summary')
    table.add_column('Test Name', style='cyan')
    table.add_column('Status', style='green')
    table.add_column('Duration (ms)', style='yellow', justify='right')
    table.add_column('Response Size', style='blue', justify='right')
    table.add_column('Notes', style='magenta')

    successful_tests = [r for r in self.results if r['success']]
    failed_tests = [r for r in self.results if not r['success']]

    # Sort by duration (slowest first)
    sorted_results = sorted(self.results, key=lambda x: x['duration_ms'], reverse=True)

    for result in sorted_results:
      status = '✅ OK' if result['success'] else '❌ FAIL'

      # Format response size
      size_mb = result['response_size_bytes'] / (1024 * 1024)
      if size_mb > 1:
        size_str = f'{size_mb:.2f} MB'
      elif result['response_size_bytes'] > 1024:
        size_str = f'{result["response_size_bytes"] / 1024:.1f} KB'
      else:
        size_str = f'{result["response_size_bytes"]} B'

      # Add notes
      notes = []
      if 'traces_count' in result:
        notes.append(f'{result["traces_count"]} traces')
      if result['duration_ms'] > 1000:
        notes.append('SLOW')
      if not result['success'] and 'error' in result:
        notes.append(f'Error: {result["error"][:50]}...')

      table.add_row(
        result['test_name'], status, f'{result["duration_ms"]:.1f}', size_str, ', '.join(notes)
      )

    self.console.print(table)

    # Performance insights
    self.console.print('\n[bold yellow]🔍 Performance Insights[/bold yellow]')

    if successful_tests:
      avg_duration = sum(r['duration_ms'] for r in successful_tests) / len(successful_tests)
      slowest = max(successful_tests, key=lambda x: x['duration_ms'])
      fastest = min(successful_tests, key=lambda x: x['duration_ms'])

      self.console.print(f'• Average response time: {avg_duration:.1f}ms')
      self.console.print(
        f'• Slowest endpoint: {slowest["test_name"]} ({slowest["duration_ms"]:.1f}ms)'
      )
      self.console.print(
        f'• Fastest endpoint: {fastest["test_name"]} ({fastest["duration_ms"]:.1f}ms)'
      )

      # Identify bottlenecks
      slow_tests = [r for r in successful_tests if r['duration_ms'] > 1000]
      if slow_tests:
        self.console.print(f'\n[red]🐌 Slow Endpoints (>1s): {len(slow_tests)} found[/red]')
        for test in slow_tests:
          self.console.print(f'  - {test["test_name"]}: {test["duration_ms"]:.1f}ms')

      # Identify N+1 problems
      trace_tests = [r for r in successful_tests if 'Individual Trace' in r['test_name']]
      if len(trace_tests) > 1:
        total_trace_time = sum(r['duration_ms'] for r in trace_tests)
        avg_trace_time = total_trace_time / len(trace_tests)
        self.console.print('\n[yellow]🔄 N+1 Query Analysis:[/yellow]')
        self.console.print(f'  - {len(trace_tests)} individual trace requests')
        self.console.print(f'  - Average time per trace: {avg_trace_time:.1f}ms')
        self.console.print(f'  - Total time for all traces: {total_trace_time:.1f}ms')
        self.console.print('  - Potential for batch optimization!')

    if failed_tests:
      self.console.print(f'\n[red]❌ Failed Tests: {len(failed_tests)}[/red]')
      for test in failed_tests:
        error_msg = test.get('error', 'Unknown error')[:100]
        self.console.print(f'  - {test["test_name"]}: {error_msg}')

  def save_results(self) -> None:
    """Save detailed results to JSON file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'claude_scripts/performance_results_{timestamp}.json'

    with open(filename, 'w') as f:
      json.dump(
        {
          'timestamp': datetime.now().isoformat(),
          'test_summary': {
            'total_tests': len(self.results),
            'successful_tests': len([r for r in self.results if r['success']]),
            'failed_tests': len([r for r in self.results if not r['success']]),
          },
          'results': self.results,
        },
        f,
        indent=2,
      )

    self.console.print(f'\n💾 Detailed results saved to: {filename}')


async def main():
  """Main entry point for performance testing."""
  analyzer = PerformanceAnalyzer()
  await analyzer.run_comprehensive_test()


if __name__ == '__main__':
  asyncio.run(main())
