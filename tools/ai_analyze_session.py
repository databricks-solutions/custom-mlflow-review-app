#!/usr/bin/env python3
"""AI-Powered Labeling Session Analysis Tool

CLI tool for comprehensive analysis of SME labeling session results.
Uses shared utilities from labeling_session_analysis module.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from utils.config import config
from utils.labeling_session_analysis import analyze_labeling_session_complete


async def analyze_session_with_report(
  review_app_id: str,
  session_id: str,
  include_ai: bool = True,
  model_endpoint: str = None,
) -> dict:
  """Analyze session and generate markdown report using enhanced methodology."""
  print('🔄 Analyzing labeling session with enhanced methodology...')

  # Run complete analysis with config fallback
  model_endpoint = model_endpoint or config.model_endpoint
  analysis_results = await analyze_labeling_session_complete(
    review_app_id=review_app_id,
    session_id=session_id,
    include_ai_insights=include_ai,
    model_endpoint=model_endpoint,
    store_to_mlflow=True,  # Always store to MLflow
  )

  if analysis_results['status'] != 'success':
    return analysis_results

  # Check storage result
  storage = analysis_results.get('storage')
  if storage and not storage.get('error'):
    print(f"✅ Analysis stored to MLflow run {storage.get('run_id')}")
    print(f"   - Report: {storage.get('report_path')}")
    print(f"   - Data: {storage.get('data_path')}")
  elif storage and storage.get('error'):
    print(f"⚠️ Failed to store to MLflow: {storage.get('error')}")
  else:
    print('⚠️ No MLflow run ID found for session')

  return analysis_results


def print_analysis_result(result: dict, format_type: str):
  """Print analysis results in specified format."""
  if format_type == 'json':
    # Exclude the full report and large data for JSON output
    output = {
      'status': result.get('status'),
      'session_id': result.get('session_id'),
      'metrics': result.get('metrics'),
      'statistics': result.get('statistics'),
      'insights': result.get('insights'),
      'storage': result.get('storage'),
      'has_experiment_context': result.get('has_experiment_context'),
    }
    print(json.dumps(output, indent=2, default=str))
  else:
    # Print the markdown report
    print(result.get('report', 'No report generated'))


async def main():
  """CLI entry point."""
  parser = argparse.ArgumentParser(
    description='Analyze labeling session results with comprehensive statistics and insights',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Analyze a labeling session
  python tools/ai_analyze_session.py --review-app-id abc123 --session-id def456
  
  # Without AI synthesis (faster)
  python tools/ai_analyze_session.py --review-app-id abc123 --session-id def456 --no-ai
  
  # Output as JSON for further processing
  python tools/ai_analyze_session.py --review-app-id abc123 --session-id def456 --format json
  
  # Use custom model endpoint
  python tools/ai_analyze_session.py --review-app-id abc123 --session-id def456 --model databricks-dbrx
        """,
  )

  parser.add_argument('--review-app-id', required=True, help='Review app ID')
  parser.add_argument('--session-id', required=True, help='Labeling session ID')
  parser.add_argument('--no-ai', action='store_true', help='Skip AI-generated insights')
  parser.add_argument(
    '--model', default=None, help='Model endpoint for AI insights (default: from MODEL_ENDPOINT env var)'
  )
  parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')

  args = parser.parse_args()

  print('🔬 Labeling Session Analysis')
  print('=' * 50)

  try:
    result = await analyze_session_with_report(
      review_app_id=args.review_app_id,
      session_id=args.session_id,
      include_ai=not args.no_ai,
      model_endpoint=args.model,
    )

    print_analysis_result(result, args.format)

    if result.get('status') == 'success':
      print('\n✅ Analysis completed successfully!')
    else:
      print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
      sys.exit(1)

  except KeyboardInterrupt:
    print('\n⚠️ Analysis interrupted by user')
    sys.exit(1)
  except Exception as e:
    print(f'\n❌ Unexpected error: {e}')
    import traceback

    traceback.print_exc()
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
