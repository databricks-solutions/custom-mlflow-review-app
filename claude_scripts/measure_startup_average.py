#!/usr/bin/env python3
"""Measure FastAPI app startup time with multiple runs for average."""

import gc
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print('📊 Measuring FastAPI app startup time (5 runs for average)')
print('=' * 60)

startup_times = []

for run in range(5):
  print(f'\n🔄 Run {run + 1}/5:')

  # Clear module cache and garbage collect for clean measurement
  modules_to_remove = [m for m in sys.modules.keys() if m.startswith('server.')]
  for module in modules_to_remove:
    if module in sys.modules:
      del sys.modules[module]
  gc.collect()

  # Record start time
  start_time = time.time()

  try:
    # Import server.app which triggers all the initialization
    from server.app import app

    # Total startup time
    total_time = time.time() - start_time
    startup_times.append(total_time)

    print(f'   ✅ Completed in {total_time * 1000:.1f}ms')

    # Clean up for next run
    del app

  except Exception as e:
    error_time = time.time() - start_time
    print(f'   ❌ Failed after {error_time * 1000:.1f}ms: {str(e)}')

if startup_times:
  # Calculate statistics
  avg_time = sum(startup_times) / len(startup_times)
  min_time = min(startup_times)
  max_time = max(startup_times)

  print('\n' + '=' * 60)
  print('📈 STARTUP TIME STATISTICS:')
  print(f'  • Average: {avg_time * 1000:.1f}ms ({avg_time:.3f}s)')
  print(f'  • Minimum: {min_time * 1000:.1f}ms ({min_time:.3f}s)')
  print(f'  • Maximum: {max_time * 1000:.1f}ms ({max_time:.3f}s)')
  print(
    f'  • Std Dev: {((sum((t - avg_time)**2 for t in startup_times) / len(startup_times)) ** 0.5) * 1000:.1f}ms'
  )

  print(f'\n🎯 RESULT: The FastAPI app takes ~{avg_time * 1000:.0f}ms to start up')
else:
  print('❌ No successful startup measurements')
