#!/usr/bin/env python3
"""Endpoint catalog script to systematically test all FastAPI endpoints.

This script explores all available endpoints from the OpenAPI spec and provides
detailed analysis of their methods, parameters, and expected performance characteristics.
"""

import asyncio
import json
from typing import Any, Dict, List

import httpx
from rich.console import Console
from rich.table import Table


class EndpointCatalog:
  """Catalog and analyze all FastAPI endpoints from OpenAPI spec."""

  def __init__(self, base_url: str = 'http://localhost:8000'):
    self.base_url = base_url
    self.console = Console()
    self.endpoints: List[Dict[str, Any]] = []

  async def load_openapi_spec(self) -> Dict[str, Any]:
    """Load the OpenAPI specification from the server."""
    async with httpx.AsyncClient() as client:
      try:
        response = await client.get(f'{self.base_url}/openapi.json')
        response.raise_for_status()
        return response.json()
      except Exception as e:
        self.console.print(f'[red]Failed to load OpenAPI spec: {e}[/red]')
        return {}

  def analyze_endpoints(self, openapi_spec: Dict[str, Any]) -> None:
    """Analyze all endpoints from OpenAPI specification."""
    paths = openapi_spec.get('paths', {})

    for path, methods in paths.items():
      for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
          endpoint_info = {
            'path': path,
            'method': method.upper(),
            'summary': details.get('summary', ''),
            'description': details.get('description', ''),
            'tags': details.get('tags', []),
            'parameters': self._extract_parameters(details),
            'request_body': self._extract_request_body(details),
            'responses': details.get('responses', {}),
            'performance_category': self._categorize_endpoint(path, method),
            'complexity': self._assess_complexity(path, details),
          }
          self.endpoints.append(endpoint_info)

  def _extract_parameters(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract parameter information from endpoint details."""
    parameters = []
    for param in details.get('parameters', []):
      parameters.append(
        {
          'name': param.get('name'),
          'location': param.get('in'),  # query, path, header
          'required': param.get('required', False),
          'type': param.get('schema', {}).get('type', ''),
          'description': param.get('description', ''),
        }
      )
    return parameters

  def _extract_request_body(self, details: Dict[str, Any]) -> Dict[str, Any]:
    """Extract request body information."""
    request_body = details.get('requestBody', {})
    if not request_body:
      return {}

    content = request_body.get('content', {})
    json_content = content.get('application/json', {})

    return {
      'required': request_body.get('required', False),
      'schema': json_content.get('schema', {}),
      'description': request_body.get('description', ''),
    }

  def _categorize_endpoint(self, path: str, method: str) -> str:
    """Categorize endpoint by expected performance characteristics."""
    if '/traces/' in path and method == 'GET':
      return 'HIGH_LATENCY'  # Individual trace fetching
    elif '/search-traces' in path:
      return 'HIGH_LATENCY'  # Complex search operations
    elif '/labeling-sessions/' in path and '/items' in path:
      return 'MEDIUM_LATENCY'  # Labeling operations
    elif method in ['POST', 'PUT', 'PATCH']:
      return 'MEDIUM_LATENCY'  # Write operations
    elif path in ['/health', '/api/config/']:
      return 'LOW_LATENCY'  # Simple operations
    else:
      return 'MEDIUM_LATENCY'

  def _assess_complexity(self, path: str, details: Dict[str, Any]) -> str:
    """Assess endpoint complexity based on parameters and path."""
    param_count = len(details.get('parameters', []))
    has_request_body = 'requestBody' in details
    path_params = path.count('{')

    complexity_score = param_count + (2 if has_request_body else 0) + path_params

    if complexity_score <= 1:
      return 'LOW'
    elif complexity_score <= 4:
      return 'MEDIUM'
    else:
      return 'HIGH'

  def display_catalog(self) -> None:
    """Display comprehensive endpoint catalog."""
    if not self.endpoints:
      self.console.print('[red]No endpoints found[/red]')
      return

    self.console.print('[bold blue]📚 Complete FastAPI Endpoint Catalog[/bold blue]\n')

    # Group by performance category
    categories = {}
    for endpoint in self.endpoints:
      category = endpoint['performance_category']
      if category not in categories:
        categories[category] = []
      categories[category].append(endpoint)

    for category, endpoints in categories.items():
      # Create table for this category
      table = Table(title=f'{category} Endpoints ({len(endpoints)} total)')
      table.add_column('Method', style='cyan', width=8)
      table.add_column('Path', style='green', width=40)
      table.add_column('Summary', style='yellow', width=30)
      table.add_column('Complexity', style='red', width=10)
      table.add_column('Parameters', style='blue', width=15)

      for endpoint in sorted(endpoints, key=lambda x: (x['method'], x['path'])):
        # Format parameters
        params = endpoint.get('parameters', [])
        param_str = f'{len(params)} params'
        if params:
          required_params = [p['name'] for p in params if p['required']]
          if required_params:
            param_str += f' ({len(required_params)} req)'

        table.add_row(
          endpoint['method'],
          endpoint['path'],
          endpoint['summary'][:50] + ('...' if len(endpoint['summary']) > 50 else ''),
          endpoint['complexity'],
          param_str,
        )

      self.console.print(table)
      self.console.print()

  def get_performance_test_endpoints(self) -> Dict[str, List[Dict[str, Any]]]:
    """Get endpoints organized for performance testing."""
    test_groups = {
      'basic_health': [],
      'high_latency_read': [],
      'medium_latency_read': [],
      'write_operations': [],
      'complex_operations': [],
    }

    for endpoint in self.endpoints:
      if endpoint['path'] in ['/health', '/api/config/']:
        test_groups['basic_health'].append(endpoint)
      elif endpoint['performance_category'] == 'HIGH_LATENCY' and endpoint['method'] == 'GET':
        test_groups['high_latency_read'].append(endpoint)
      elif endpoint['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']:
        test_groups['write_operations'].append(endpoint)
      elif endpoint['complexity'] == 'HIGH':
        test_groups['complex_operations'].append(endpoint)
      else:
        test_groups['medium_latency_read'].append(endpoint)

    return test_groups

  def save_catalog(self) -> None:
    """Save endpoint catalog to JSON file."""
    filename = 'claude_scripts/endpoint_catalog.json'

    catalog_data = {
      'total_endpoints': len(self.endpoints),
      'categories': {},
      'endpoints': self.endpoints,
      'performance_test_groups': self.get_performance_test_endpoints(),
    }

    # Calculate category stats
    for endpoint in self.endpoints:
      category = endpoint['performance_category']
      if category not in catalog_data['categories']:
        catalog_data['categories'][category] = 0
      catalog_data['categories'][category] += 1

    with open(filename, 'w') as f:
      json.dump(catalog_data, f, indent=2)

    self.console.print(f'💾 Endpoint catalog saved to: {filename}')

  async def run_catalog_analysis(self) -> None:
    """Run complete endpoint catalog analysis."""
    self.console.print('[bold blue]🔍 Loading and analyzing FastAPI endpoints...[/bold blue]')

    # Load OpenAPI spec
    openapi_spec = await self.load_openapi_spec()
    if not openapi_spec:
      return

    # Analyze endpoints
    self.analyze_endpoints(openapi_spec)

    # Display results
    self.display_catalog()

    # Show performance insights
    self.console.print('[bold yellow]🎯 Performance Testing Insights[/bold yellow]')
    test_groups = self.get_performance_test_endpoints()

    for group_name, endpoints in test_groups.items():
      if endpoints:
        self.console.print(f'• {group_name.replace("_", " ").title()}: {len(endpoints)} endpoints')
        for endpoint in endpoints[:3]:  # Show first 3 as examples
          self.console.print(f'  - {endpoint["method"]} {endpoint["path"]}')
        if len(endpoints) > 3:
          self.console.print(f'  ... and {len(endpoints) - 3} more')

    # Save catalog
    self.save_catalog()


async def main():
  """Main entry point for endpoint catalog analysis."""
  catalog = EndpointCatalog()
  await catalog.run_catalog_analysis()


if __name__ == '__main__':
  asyncio.run(main())
