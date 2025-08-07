#!/usr/bin/env python3
"""Measure actual Uvicorn server startup time."""

import os
import signal
import subprocess
import time

import requests

print('🚀 Measuring Uvicorn server startup time')
print('=' * 50)


def find_free_port():
  """Find a free port to use for testing."""
  import socket

  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('', 0))
    s.listen(1)
    port = s.getsockname()[1]
  return port


# Find a free port
port = find_free_port()
print(f'🔌 Using port {port}')

# Record start time
start_time = time.time()

# Start uvicorn server in background
print('🎬 Starting Uvicorn server...')
uvicorn_cmd = ['uv', 'run', 'uvicorn', 'server.app:app', '--host', '0.0.0.0', '--port', str(port)]

process = subprocess.Popen(
  uvicorn_cmd,
  stdout=subprocess.PIPE,
  stderr=subprocess.STDOUT,
  text=True,
  preexec_fn=os.setsid,  # Create new process group
)

# Wait for server to be ready by polling health endpoint
max_wait = 30  # seconds
poll_interval = 0.1  # seconds
ready = False
first_response_time = None

print(f'⏳ Waiting for server to respond on http://localhost:{port}/health')

for attempt in range(int(max_wait / poll_interval)):
  try:
    response = requests.get(f'http://localhost:{port}/health', timeout=1)
    if response.status_code == 200:
      if first_response_time is None:
        first_response_time = time.time()
        ready = True
        break
  except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
    pass

  time.sleep(poll_interval)

# Calculate total startup time
if ready:
  startup_time = first_response_time - start_time
  print(f'✅ Server responded after {startup_time * 1000:.1f}ms ({startup_time:.3f}s)')

  # Test a few more endpoints to make sure everything is working
  print('🧪 Testing additional endpoints...')

  endpoints_to_test = [
    f'http://localhost:{port}/health',
    f'http://localhost:{port}/api/config/',
  ]

  for endpoint in endpoints_to_test:
    try:
      resp = requests.get(endpoint, timeout=2)
      print(f"   • {endpoint.split('/')[-2:]}: {resp.status_code} ({len(resp.text)} chars)")
    except Exception as e:
      print(f'   • {endpoint}: ERROR - {str(e)}')
else:
  print(f'❌ Server failed to start within {max_wait} seconds')
  startup_time = None

# Clean up - terminate the process group
print('🧹 Cleaning up server process...')
try:
  # Terminate the entire process group
  os.killpg(os.getpgid(process.pid), signal.SIGTERM)
  process.wait(timeout=5)
except (subprocess.TimeoutExpired, ProcessLookupError):
  # Force kill if it doesn't terminate gracefully
  try:
    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
  except ProcessLookupError:
    pass

if ready:
  print('=' * 50)
  print(f'🎯 UVICORN STARTUP TIME: {startup_time * 1000:.1f}ms ({startup_time:.3f}s)')
  print('📊 This includes:')
  print('   • FastAPI app initialization (~377ms average)')
  print('   • Uvicorn server setup and binding')
  print('   • Network socket ready to accept requests')
else:
  print('💥 Measurement failed - server did not start properly')
