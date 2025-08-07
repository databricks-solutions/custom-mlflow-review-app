#!/usr/bin/env python3
"""Detailed breakdown of startup timing by analyzing what happens INSIDE each import."""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print('🔬 DETAILED STARTUP BREAKDOWN - ANALYZING WHAT HAPPENS INSIDE IMPORTS')
print('=' * 80)

# Let's manually trace what happens when we import server.app
print('🚀 Step-by-step analysis of server.app import...')

# Clear any cached modules first
import gc


def clear_server_modules():
  """Clear all server.* modules from cache."""
  to_remove = [k for k in sys.modules.keys() if k.startswith('server.')]
  for module in to_remove:
    if module in sys.modules:
      del sys.modules[module]
  gc.collect()


def time_import_with_analysis(description, import_func):
  """Import with detailed timing analysis."""
  print(f'\n📦 {description}')
  print('-' * 60)

  start = time.time()
  result = import_func()
  total = time.time() - start

  print(f'✅ Completed: {total*1000:.1f}ms')
  return result, total


# Start clean
clear_server_modules()

# Step 1: Import just the basic dependencies of server.app
print('\n🔍 STEP 1: Basic Dependencies')


def import_basic_deps():
  return 'basic deps loaded'


basic_deps, basic_time = time_import_with_analysis('Basic FastAPI dependencies', import_basic_deps)


# Step 2: Import middleware (should be fast)
def import_middleware():
  return 'middleware loaded'


middleware, middleware_time = time_import_with_analysis('Server middleware', import_middleware)


# Step 3: Import routers (this is where the slowness likely occurs)
def import_routers():
  from server.routers import router

  return router


router_obj, router_time = time_import_with_analysis('Server routers (THE SUSPECT)', import_routers)

print(f"\n{'='*80}")
print('📊 TIMING BREAKDOWN')
print(f"{'='*80}")
print(f'Basic FastAPI deps:     {basic_time*1000:>8.1f}ms')
print(f'Server middleware:      {middleware_time*1000:>8.1f}ms')
print(f'Server routers:         {router_time*1000:>8.1f}ms  🔥 BOTTLENECK')
print(f'Total measured:         {(basic_time + middleware_time + router_time)*1000:>8.1f}ms')

# Now let's dig into what the router import does
print(f"\n{'='*80}")
print('🕵️ INVESTIGATING ROUTER IMPORT BOTTLENECK')
print(f"{'='*80}")

# Clear modules again to get clean measurements
clear_server_modules()

# Let's trace individual router imports
router_modules = [
  ('server.routers.core', 'Core router (config, user, auth)'),
  ('server.routers.managed_evals', 'Managed evals router'),
  ('server.routers.mlflow', 'MLflow router'),
  ('server.routers.review', 'Review apps router'),
  ('server.routers.traces.analysis', 'Traces analysis router'),
  ('server.routers.traces.assessments', 'Traces assessments router'),
]

router_times = {}

for module_name, description in router_modules:
  # Clear server modules before each import
  to_remove = [k for k in sys.modules.keys() if k.startswith('server.')]
  for module in to_remove:
    if module in sys.modules:
      del sys.modules[module]

  def import_single_router():
    return __import__(module_name, fromlist=[''])

  _, import_time = time_import_with_analysis(description, import_single_router)
  router_times[module_name] = import_time

# Show router timing breakdown
print('\n🚀 ROUTER IMPORT BREAKDOWN:')
sorted_routers = sorted(router_times.items(), key=lambda x: x[1], reverse=True)
for module, import_time in sorted_routers:
  print(f'  {module:<35} {import_time*1000:>6.1f}ms')

# Now let's specifically check what's in the slowest router
slowest_router = sorted_routers[0][0]
print(f'\n🔍 INVESTIGATING SLOWEST ROUTER: {slowest_router}')

# Let's check what utility classes get imported
print(f"\n{'='*80}")
print('🛠️  CHECKING UTILITY CLASS INSTANTIATIONS')
print(f"{'='*80}")

# Clear modules
clear_server_modules()

# Check each utility class individually
utility_classes = [
  ('server.utils.mlflow_utils', 'MLflowUtils class - creates MlflowClient()'),
  ('server.utils.review_apps_utils', 'ReviewAppsUtils class - calls mlflow.set_tracking_uri()'),
  (
    'server.utils.labeling_sessions_utils',
    'LabelingSessionsUtils class - calls mlflow.set_tracking_uri()',
  ),
  ('server.utils.config', 'Config loading and parsing'),
  ('server.utils.proxy', 'HTTP proxy utilities'),
  ('server.utils.databricks_auth', 'Databricks authentication utilities'),
]

utility_times = {}

for module_name, description in utility_classes:
  # Clear server modules before each test
  to_remove = [k for k in sys.modules.keys() if k.startswith('server.')]
  for module in to_remove:
    if module in sys.modules:
      del sys.modules[module]

  def import_utility():
    return __import__(module_name, fromlist=[''])

  _, import_time = time_import_with_analysis(description, import_utility)
  utility_times[module_name] = import_time

# Show utility timing breakdown
print('\n🛠️  UTILITY IMPORT BREAKDOWN:')
sorted_utilities = sorted(utility_times.items(), key=lambda x: x[1], reverse=True)
for module, import_time in sorted_utilities:
  print(f'  {module:<35} {import_time*1000:>6.1f}ms')

print(f"\n{'='*80}")
print('🎯 FINAL ANALYSIS')
print(f"{'='*80}")

total_router_time = sum(router_times.values())
total_utility_time = sum(utility_times.values())

print(f'Total router imports:   {total_router_time*1000:>8.1f}ms')
print(f'Total utility imports:  {total_utility_time*1000:>8.1f}ms')
print(
  f'Expected overlap:       {max(total_router_time, total_utility_time)*1000:>8.1f}ms (utilities imported by routers)'
)

print('\n🔥 BOTTLENECK IDENTIFICATION:')
if total_router_time > 500:
  print(f'  • Router imports are the bottleneck ({total_router_time*1000:.0f}ms)')
else:
  print(f'  • Utility imports are the bottleneck ({total_utility_time*1000:.0f}ms)')

print('\n⚡ SPECIFIC RECOMMENDATIONS:')
print(f'  1. The slowest router is: {sorted_routers[0][0]} ({sorted_routers[0][1]*1000:.0f}ms)')
print(
  f'  2. The slowest utility is: {sorted_utilities[0][0]} ({sorted_utilities[0][1]*1000:.0f}ms)'
)
print('  3. Focus optimization on the top 2-3 slowest components')
