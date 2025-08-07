#!/usr/bin/env python3
"""Databricks App Client for making authenticated requests to live Databricks Apps.

Based on authentication patterns from databricks-solutions/custom-mcp-databricks-app.
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')


class DatabricksAppClient:
  """Client for making authenticated requests to Databricks Apps."""

  def __init__(self, app_url: str, host: str = None, profile: str = None):
    """Initialize client with app URL.

    Args:
        app_url: Base URL of the Databricks app
        host: Databricks workspace host URL (optional)
        profile: Databricks CLI profile name (optional)
    """
    self.app_url = app_url.rstrip('/')
    self.host = host
    self.profile = profile
    self._token_cache: Optional[str] = None

  def _get_oauth_token(self) -> str:
    """Get OAuth token using Databricks CLI."""
    try:
      # Use provided profile, host, or fall back to environment
      cmd = ['databricks', 'auth', 'token']

      if self.profile:
        cmd.extend(['--profile', self.profile])
      elif self.host:
        cmd.extend(['--host', self.host])
      else:
        host = os.getenv('DATABRICKS_HOST')
        if not host:
          raise Exception(
            'DATABRICKS_HOST environment variable not set and no --host or --profile provided'
          )
        cmd.extend(['--host', host])

      # Try to get existing token first
      result = subprocess.run(cmd, capture_output=True, text=True, check=False)

      if result.returncode == 0 and result.stdout.strip():
        token_output = result.stdout.strip()
        # Parse JSON if the output is JSON formatted
        try:
          token_data = json.loads(token_output)
          token = token_data.get('access_token', token_output)
        except json.JSONDecodeError:
          token = token_output

        # Validate token
        if self._validate_token(token):
          return token

      # If no valid token, try to login
      print('No valid token found, attempting to login...')
      login_cmd = ['databricks', 'auth', 'login']

      if self.profile:
        login_cmd.extend(['--profile', self.profile])
      elif self.host:
        login_cmd.extend(['--host', self.host])
      else:
        host = os.getenv('DATABRICKS_HOST')
        login_cmd.extend(['--host', host])

      login_result = subprocess.run(login_cmd, capture_output=True, text=True, check=False)

      if login_result.returncode != 0:
        raise Exception(f'Failed to login: {login_result.stderr}')

      # Get token after login
      token_result = subprocess.run(cmd, capture_output=True, text=True, check=True)

      token_output = token_result.stdout.strip()
      # Parse JSON if the output is JSON formatted
      try:
        token_data = json.loads(token_output)
        return token_data.get('access_token', token_output)
      except json.JSONDecodeError:
        return token_output

    except subprocess.CalledProcessError as e:
      raise Exception(f'Failed to get OAuth token: {e}')
    except FileNotFoundError:
      raise Exception('Databricks CLI not found. Please install databricks CLI.')

  def _validate_token(self, token: str) -> bool:
    """Validate token by making a request to SCIM endpoint."""
    try:
      headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

      # Use the workspace host from environment
      import os

      workspace_host = os.getenv('DATABRICKS_HOST')
      if not workspace_host:
        return False

      response = requests.get(
        f'{workspace_host}/api/2.0/preview/scim/v2/Me', headers=headers, timeout=10
      )

      return response.status_code == 200

    except Exception:
      return False

  def _get_headers(self) -> Dict[str, str]:
    """Get request headers with authentication."""
    if not self._token_cache or not self._validate_token(self._token_cache):
      self._token_cache = self._get_oauth_token()

    headers = {
      'Authorization': f'Bearer {self._token_cache}',
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
    }

    print(f'DEBUG: Using token authentication (token preview: {self._token_cache[:50]}...)')

    return headers

  def get(
    self, endpoint: str, params: Optional[Dict[str, Any]] = None, return_text: bool = False
  ) -> Any:
    """Make GET request to the app."""
    url = f'{self.app_url}{endpoint}'
    headers = self._get_headers()

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    if return_text:
      return response.text

    if response.text:
      try:
        return response.json()
      except json.JSONDecodeError:
        return response.text
    return {}

  def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make POST request to the app."""
    url = f'{self.app_url}{endpoint}'
    headers = self._get_headers()

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    if response.text:
      return response.json()
    return {}

  def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make PUT request to the app."""
    url = f'{self.app_url}{endpoint}'
    headers = self._get_headers()

    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

    if response.text:
      return response.json()
    return {}

  def delete(self, endpoint: str) -> Dict[str, Any]:
    """Make DELETE request to the app."""
    url = f'{self.app_url}{endpoint}'
    headers = self._get_headers()

    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    if response.text:
      return response.json()
    return {}


def main():
  """CLI interface for testing the client."""
  import argparse

  parser = argparse.ArgumentParser(
    description='Databricks App Client for making authenticated requests',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python dba_client.py https://my-app.aws.databricksapps.com /api/config/
  python dba_client.py https://my-app.aws.databricksapps.com /api/user/me --profile my-profile
  python dba_client.py https://my-app.aws.databricksapps.com /api/data POST '{"key":"value"}' \\
      --host https://workspace.cloud.databricks.com
        """,
  )

  parser.add_argument('app_url', help='Base URL of the Databricks app')
  parser.add_argument('endpoint', help='API endpoint to call')
  parser.add_argument(
    'method', nargs='?', default='GET', help='HTTP method (GET, POST, PUT, DELETE)'
  )
  parser.add_argument('data', nargs='?', help='JSON data for POST/PUT requests')
  parser.add_argument('--host', help='Databricks workspace host URL')
  parser.add_argument('--profile', help='Databricks CLI profile name')

  args = parser.parse_args()

  client = DatabricksAppClient(args.app_url, host=args.host, profile=args.profile)

  try:
    method = args.method.upper()

    if method == 'GET':
      result = client.get(args.endpoint)
    elif method == 'POST':
      data = json.loads(args.data) if args.data else None
      result = client.post(args.endpoint, data)
    elif method == 'PUT':
      data = json.loads(args.data) if args.data else None
      result = client.put(args.endpoint, data)
    elif method == 'DELETE':
      result = client.delete(args.endpoint)
    else:
      print(f'Unsupported method: {method}')
      sys.exit(1)

    if isinstance(result, dict):
      print(json.dumps(result, indent=2))
    else:
      print(result)

  except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
