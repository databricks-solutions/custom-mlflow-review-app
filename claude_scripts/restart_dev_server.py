#!/usr/bin/env python3
"""Restart development server cleanly and test performance."""

import os
import signal
import subprocess
import time

import requests


def kill_dev_servers():
  """Kill existing development servers."""
  print('🧹 Cleaning up existing servers...')

  # Kill processes on common ports
  for port in [5173, 8000]:
    try:
      result = subprocess.run(
        ['lsof', '-ti', f':{port}'], capture_output=True, text=True, check=False
      )

      if result.stdout.strip():
        pids = result.stdout.strip().split('\n')
        for pid in pids:
          try:
            print(f'  💀 Killing PID {pid} on port {port}')
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)
          except (ValueError, ProcessLookupError):
            pass
      else:
        print(f'  ✅ Port {port} is free')

    except Exception:
      print(f'  ✅ Port {port} is free')

  # Kill watch.sh and uvicorn processes
  for cmd in ['watch.sh', 'uvicorn']:
    try:
      subprocess.run(['pkill', '-f', cmd], check=False, capture_output=True)
      print(f'  💀 Killed {cmd} processes')
    except:
      pass

  time.sleep(2)
  print('✅ Cleanup complete')


def start_backend_with_profiling():
  """Start backend with our new profiling enabled."""
  print('🚀 Starting backend with performance profiling...')

  env = os.environ.copy()
  # Ensure logging level is set for our profiling
  env['PYTHONPATH'] = '.'

  cmd = [
    'uv',
    'run',
    'uvicorn',
    'server.app:app',
    '--host',
    '0.0.0.0',
    '--port',
    '8000',
    '--log-level',
    'info',  # Enable detailed logging
  ]

  print(f"💻 Command: {' '.join(cmd)}")

  # Start server and capture output
  process = subprocess.Popen(
    cmd,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    universal_newlines=True,
  )

  print(f'🎯 Backend PID: {process.pid}')

  # Wait for startup and show logs
  print('⏳ Waiting for startup (showing logs)...')
  startup_timeout = 15
  start_time = time.time()

  while time.time() - start_time < startup_timeout:
    # Check if server is ready
    try:
      response = requests.get('http://localhost:8000/health', timeout=2)
      if response.status_code == 200:
        print(f'✅ Server ready! Health check: {response.status_code}')
        break
    except:
      pass

    time.sleep(1)
    print('  ⏳ Still starting up...')

  else:
    print('⚠️  Startup timeout - server may still be loading')

  return process


def test_slow_endpoint():
  """Test the problematic endpoint with detailed timing."""
  print('\n🧪 Testing slow endpoint with profiling...')

  endpoint = 'http://localhost:8000/api/review-apps/36cb6150924443a9a8abf3209bcffaf8'

  print(f'📡 Testing: {endpoint}')

  try:
    start_time = time.time()
    response = requests.get(endpoint, timeout=45)
    elapsed = time.time() - start_time

    print(f'✅ Response: {response.status_code} in {elapsed*1000:.1f}ms')

    # Check for our custom timing headers
    if 'X-Response-Time' in response.headers:
      print(f"⏱️  Server timing: {response.headers['X-Response-Time']}")

    if response.status_code == 200:
      try:
        data = response.json()
        print(f"📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
      except:
        print('📄 Response is not JSON')
    else:
      print(f'❌ Error response: {response.text[:200]}...')

  except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f'⏰ TIMEOUT after {elapsed*1000:.1f}ms')

  except Exception as e:
    elapsed = time.time() - start_time
    print(f'💥 ERROR after {elapsed*1000:.1f}ms: {str(e)}')


def main():
  print('🔧 Development Server Performance Debug')
  print('=' * 45)

  # Step 1: Clean restart
  kill_dev_servers()

  # Step 2: Start with profiling
  backend_process = start_backend_with_profiling()

  if not backend_process:
    print('❌ Failed to start backend')
    return

  try:
    # Step 3: Test the slow endpoint
    test_slow_endpoint()

    print('\n💡 Backend is running with profiling enabled')
    print('📋 Now check server logs for detailed performance traces:')
    print('   🌐 [DATABRICKS ASYNC/SYNC] - API calls')
    print('   🧬 [MLFLOW GENAI] - MLflow SDK calls')
    print('   🔍 [MLFLOW SDK] - MLflow operations')
    print('   🐌 [SLOW ENDPOINT] - Endpoints over 500ms')
    print('   🔍 [PROFILE] - Detailed function profiling')
    print('\n⏹️  Press Ctrl+C to stop')

    # Keep running and show any output
    while True:
      time.sleep(1)

  except KeyboardInterrupt:
    print('\n🛑 Stopping backend...')
    backend_process.terminate()
    time.sleep(3)
    if backend_process.poll() is None:
      print('💀 Force killing...')
      backend_process.kill()
    print('✅ Backend stopped')


if __name__ == '__main__':
  main()
