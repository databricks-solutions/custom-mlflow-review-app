#!/usr/bin/env python3
"""Simple FastAPI app startup time measurement."""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print('📊 Measuring FastAPI app startup time...')
print('=' * 50)

# Record start time
start_time = time.time()
print('⏰ Starting measurement...')

try:
  # Import server.app which triggers all the initialization
  print('📦 Importing FastAPI app...')

  from server.app import app

  # Total startup time
  total_time = time.time() - start_time

  # Check basic app properties
  route_count = len(app.routes) if hasattr(app, 'routes') else 0

  print('=' * 50)
  print(f'🎯 TOTAL STARTUP TIME: {total_time * 1000:.1f}ms ({total_time:.3f}s)')
  print(f'📋 Routes registered: {route_count}')
  print(f'🏷️  App title: {app.title}')
  print(f'📝 App description length: {len(app.description)} characters')

  # Break down what happens during startup
  print('\n🔍 What happens during startup:')
  print('  • Load environment variables (.env, .env.local)')
  print('  • Initialize FastAPI app with middleware:')
  print('    - ErrorHandlerMiddleware')
  print('    - AuthMiddleware')
  print('    - TimingMiddleware')
  print('    - GZipMiddleware')
  print('    - CORSMiddleware')
  print('  • Include API routers:')
  print('    - Core (config, user, auth, experiment summaries)')
  print('    - MLflow (experiments, runs, traces)')
  print('    - Review Apps (review apps, labeling sessions, items)')
  print('    - Traces (analysis, assessments)')
  print('  • Mount static file serving')

except Exception as e:
  error_time = time.time() - start_time
  print(f'❌ Startup failed after {error_time * 1000:.1f}ms')
  print(f'💥 Error: {str(e)}')
  import traceback

  traceback.print_exc()
