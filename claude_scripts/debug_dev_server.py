#!/usr/bin/env python3
"""Debug development server issues and restart cleanly."""

import os
import signal
import subprocess
import time

import psutil
import requests


def kill_dev_servers():
  """Kill any existing development servers."""
  print('🧹 Killing existing development servers...')

  # Kill processes on ports 5173 and 8000
  ports_to_kill = [5173, 8000]

  for port in ports_to_kill:
    try:
      # Find processes using the port
      result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)

      if result.stdout.strip():
        pids = result.stdout.strip().split('\n')
        for pid in pids:
          try:
            print(f'  💀 Killing PID {pid} on port {port}')
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)
            # Force kill if still alive
            try:
              os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
              pass  # Already dead
          except (ValueError, ProcessLookupError):
            pass
      else:
        print(f'  ✅ No processes on port {port}')

    except subprocess.CalledProcessError:
      print(f'  ✅ No processes on port {port}')

  # Kill any remaining watch.sh processes
  try:
    subprocess.run(['pkill', '-f', 'watch.sh'], check=False)
    print('  💀 Killed watch.sh processes')
  except:
    pass

  # Kill any remaining uvicorn processes
  try:
    subprocess.run(['pkill', '-f', 'uvicorn'], check=False)
    print('  💀 Killed uvicorn processes')
  except:
    pass

  time.sleep(2)
  print('✅ Cleanup complete')


def check_server_status():
  """Check if servers are running and responding."""
  print('🔍 Checking server status...')

  servers = [
    ('Backend', 'http://localhost:8000/health'),
    ('Frontend', 'http://localhost:5173'),
  ]

  for name, url in servers:
    try:
      response = requests.get(url, timeout=5)
      print(f'  ✅ {name}: {response.status_code} - {url}')
    except requests.exceptions.ConnectionError:
      print(f'  ❌ {name}: Connection refused - {url}')
    except requests.exceptions.Timeout:
      print(f'  ⏰ {name}: Timeout - {url}')
    except Exception as e:
      print(f'  ❌ {name}: Error - {str(e)}')


def check_process_tree():
  """Check what processes are running related to the app."""
  print('🌳 Process tree:')

  keywords = ['uvicorn', 'vite', 'node', 'watch.sh', 'python']

  for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
      cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
      if any(keyword in cmdline.lower() for keyword in keywords):
        if 'server.app' in cmdline or 'watch.sh' in cmdline or 'vite' in cmdline:
          print(f"  🔍 PID {proc.info['pid']}: {cmdline[:100]}...")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
      pass


def start_backend_only():
  """Start just the backend for testing."""
  print('🚀 Starting backend server only...')

  try:
    # Start uvicorn directly
    cmd = [
      'uv',
      'run',
      'uvicorn',
      'server.app:app',
      '--host',
      '0.0.0.0',
      '--port',
      '8000',
      '--reload',
      '--reload-dir',
      'server',
    ]

    print(f"💻 Running: {' '.join(cmd)}")

    # Start in background
    process = subprocess.Popen(cmd)

    print(f'🎯 Backend PID: {process.pid}')

    # Wait a bit for startup
    print('⏳ Waiting for backend to start...')
    time.sleep(5)

    # Test if it's responding
    try:
      response = requests.get('http://localhost:8000/health', timeout=10)
      print(f'✅ Backend responding: {response.status_code}')

      # Test the slow endpoint
      print('🧪 Testing slow endpoint...')
      start = time.time()
      try:
        slow_response = requests.get(
          'http://localhost:8000/api/review-apps/36cb6150924443a9a8abf3209bcffaf8', timeout=30
        )
        elapsed = time.time() - start
        print(f'📊 Slow endpoint: {slow_response.status_code} in {elapsed*1000:.1f}ms')
      except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f'⏰ Slow endpoint TIMED OUT after {elapsed*1000:.1f}ms')
      except Exception as e:
        elapsed = time.time() - start
        print(f'❌ Slow endpoint ERROR after {elapsed*1000:.1f}ms: {str(e)}')

    except Exception as e:
      print(f'❌ Backend not responding: {str(e)}')

    return process

  except Exception as e:
    print(f'💥 Failed to start backend: {str(e)}')
    return None


def main():
  print('🔧 Development Server Debug Tool')
  print('=' * 40)

  # Step 1: Check current status
  check_process_tree()
  check_server_status()

  # Step 2: Clean shutdown
  kill_dev_servers()

  # Step 3: Check again
  print('\n📋 Status after cleanup:')
  check_process_tree()
  check_server_status()

  # Step 4: Start backend only for testing
  print('\n🧪 Starting backend for testing...')
  backend_process = start_backend_only()

  if backend_process:
    try:
      print(f'\n💡 Backend running with PID {backend_process.pid}')
      print('📋 Check logs in the terminal')
      print('⏹️  Press Ctrl+C to stop')

      # Wait for user interrupt
      backend_process.wait()

    except KeyboardInterrupt:
      print('\n🛑 Stopping backend...')
      backend_process.terminate()
      time.sleep(2)
      if backend_process.poll() is None:
        backend_process.kill()
      print('✅ Backend stopped')


if __name__ == '__main__':
  main()
