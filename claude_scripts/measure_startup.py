#!/usr/bin/env python3
"""Measure FastAPI app startup time."""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print('📊 Measuring FastAPI app startup time...')
print('=' * 50)

# Record start time
start_time = time.time()
print(f"⏰ Start time: {time.strftime('%H:%M:%S.%f', time.localtime(start_time))}")

try:
  # Import server.app which triggers all the initialization
  print('📦 Importing server.app module...')
  import_start = time.time()

  from server.app import app

  import_time = time.time() - import_start
  print(f'✅ Module import completed in {import_time * 1000:.1f}ms')

  # Check if the app is properly initialized
  print('🔍 Checking app initialization...')
  check_start = time.time()

  # Verify the app has routes
  route_count = len(app.routes)
  print(f'📋 Found {route_count} routes registered')

  # Check middleware count
  middleware_count = len(app.middleware_stack.middleware)
  print(f'🔧 Found {middleware_count} middleware layers')

  check_time = time.time() - check_start
  print(f'✅ App verification completed in {check_time * 1000:.1f}ms')

  # Total startup time
  total_time = time.time() - start_time
  print('=' * 50)
  print(f'🎯 TOTAL STARTUP TIME: {total_time * 1000:.1f}ms ({total_time:.3f}s)')

  # Breakdown
  print('\n📊 Startup Time Breakdown:')
  print(f'  • Module Import: {import_time * 1000:.1f}ms ({import_time/total_time*100:.1f}%)')
  print(f'  • App Verification: {check_time * 1000:.1f}ms ({check_time/total_time*100:.1f}%)')

except Exception as e:
  error_time = time.time() - start_time
  print(f'❌ Startup failed after {error_time * 1000:.1f}ms')
  print(f'💥 Error: {str(e)}')
  import traceback

  traceback.print_exc()
