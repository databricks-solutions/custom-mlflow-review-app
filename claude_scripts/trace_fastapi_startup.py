#!/usr/bin/env python3
"""Trace the exact FastAPI startup import chain with timing."""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print('🚀 Tracing FastAPI Startup Import Chain')
print('=' * 60)


def time_step(step_name, func):
  """Time a step and return the result and time taken."""
  start_time = time.time()
  try:
    result = func()
    elapsed = time.time() - start_time
    print(f'✅ {step_name:<40} {elapsed*1000:>6.1f}ms')
    return result, elapsed
  except Exception as e:
    elapsed = time.time() - start_time
    print(f'❌ {step_name:<40} {elapsed*1000:>6.1f}ms - {str(e)[:30]}')
    raise


def main():
  total_start = time.time()
  timing_breakdown = {}

  # Step 1: Import FastAPI core
  def import_fastapi():
    from fastapi import APIRouter

    return APIRouter

  _, timing_breakdown['fastapi_core'] = time_step('Import FastAPI Core', import_fastapi)

  # Step 2: Import server.app (the main bottleneck)
  def import_app_module():
    # This triggers the entire import chain
    import server.app

    return server.app

  _, timing_breakdown['server_app'] = time_step('Import server.app', import_app_module)

  # Step 3: Break down what server.app imports
  print(f"\n{'='*60}")
  print('🔍 BREAKDOWN OF server.app IMPORTS')
  print(f"{'='*60}")

  # These are imported by server.app
  imports_in_app = [
    ('server.middleware', 'Auth, Error, Timing middleware'),
    ('server.routers', 'All API routers'),
  ]

  for module, desc in imports_in_app:

    def import_module():
      return __import__(module, fromlist=[''])

    _, import_time = time_step(f'{module}', import_module)
    timing_breakdown[module.replace('.', '_')] = import_time

  # Step 4: Break down router imports (the suspected bottleneck)
  print(f"\n{'='*60}")
  print('🔍 BREAKDOWN OF ROUTER IMPORTS')
  print(f"{'='*60}")

  router_modules = [
    ('server.routers.core', 'Config, user, auth endpoints'),
    ('server.routers.managed_evals', 'Managed evaluations'),
    ('server.routers.mlflow', 'MLflow proxy operations'),
    ('server.routers.review', 'Review apps, sessions, items'),
    ('server.routers.traces.analysis', 'Trace analysis'),
    ('server.routers.traces.assessments', 'Trace assessments'),
  ]

  for module, desc in router_modules:

    def import_router():
      return __import__(module, fromlist=[''])

    try:
      _, import_time = time_step(f'{module}', import_router)
      timing_breakdown[module.replace('.', '_')] = import_time
    except Exception as e:
      print(f'⚠️  {module} import failed: {str(e)}')

  # Step 5: Break down utility imports (where the real work happens)
  print(f"\n{'='*60}")
  print('🔍 BREAKDOWN OF UTILITY IMPORTS (SUSPECTED BOTTLENECKS)')
  print(f"{'='*60}")

  utility_modules = [
    ('server.utils.mlflow_utils', '🔥 MLflowUtils - Creates MlflowClient()'),
    ('server.utils.review_apps_utils', '🔥 ReviewAppsUtils - mlflow.set_tracking_uri()'),
    (
      'server.utils.labeling_sessions_utils',
      '🔥 LabelingSessionsUtils - mlflow.set_tracking_uri()',
    ),
    ('server.utils.labeling_items_utils', 'LabelingItemsUtils'),
    ('server.utils.proxy', '🔥 HTTP proxy - imports MLflow auth utils'),
    ('server.utils.config', 'Config parsing'),
    ('server.utils.databricks_auth', '🔥 Databricks authentication'),
  ]

  for module, desc in utility_modules:

    def import_utility():
      return __import__(module, fromlist=[''])

    try:
      _, import_time = time_step(f'{module}', import_utility)
      timing_breakdown[module.replace('.', '_')] = import_time
    except Exception as e:
      print(f'⚠️  {module} import failed: {str(e)}')

  # Calculate total time
  total_time = time.time() - total_start

  # Summary
  print(f"\n{'='*60}")
  print('📊 STARTUP TIMING BREAKDOWN ANALYSIS')
  print(f"{'='*60}")

  # Sort by time taken
  sorted_times = sorted(timing_breakdown.items(), key=lambda x: x[1], reverse=True)

  print('🐌 SLOWEST COMPONENTS:')
  for module, import_time in sorted_times[:8]:
    percentage = (import_time / total_time) * 100
    print(f"  {module.replace('_', '.'):<35} {import_time*1000:>6.1f}ms ({percentage:>4.1f}%)")

  print(f'\n🎯 TOTAL ANALYSIS TIME: {total_time*1000:.1f}ms')

  # Identify the root causes
  print('\n🔥 ROOT CAUSE ANALYSIS:')

  # Check if MLflow import is the bottleneck
  mlflow_related = sum(
    t
    for k, t in timing_breakdown.items()
    if 'mlflow' in k or 'proxy' in k or 'databricks_auth' in k
  )

  print(
    f'  • MLflow-related imports: {mlflow_related*1000:.1f}ms ({mlflow_related/total_time*100:.1f}%)'
  )

  # Recommendations
  print('\n⚡ OPTIMIZATION RECOMMENDATIONS:')
  print('  1. Lazy load MLflow utilities (delay MlflowClient() creation)')
  print('  2. Cache Databricks credentials (avoid repeated auth lookups)')
  print('  3. Use import-time environment checks to skip expensive setups')
  print('  4. Consider moving utility instantiation from class __init__ to method calls')


if __name__ == '__main__':
  main()
