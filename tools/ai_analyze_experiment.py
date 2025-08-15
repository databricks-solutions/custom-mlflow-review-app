#!/usr/bin/env python3
"""AI-Powered Experiment Analysis Tool

Generate dynamic, intelligent analysis reports of MLflow experiments using model serving endpoints.
This tool provides comprehensive insights about agent behavior, patterns, and recommendations.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from utils.ai_analysis_utils import AIExperimentAnalyzer
from utils.config import config
from utils.mlflow_artifact_utils import MLflowArtifactManager


def print_banner():
  """Print the tool banner."""
  print('🤖 AI-Powered Experiment Analysis')
  print('=' * 50)


def write_to_mlflow_artifacts(experiment_id: str, result: dict, session_run_id: str = None):
  """Write comprehensive SME analysis to MLflow artifacts.

  Args:
      experiment_id: The experiment ID
      result: The analysis result dictionary
      session_run_id: Optional labeling session run ID to use for storage
  """
  # Initialize MLflow artifact manager
  artifact_manager = MLflowArtifactManager()

  print(f'\n📝 Storing analysis to MLflow artifacts for experiment {experiment_id}')

  # Prepare the markdown content
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  # Build the markdown content
  new_content = []

  new_content.append('# 🤖 Technical Analysis Report\n\n')
  new_content.append(f'**Generated:** {timestamp}\n')
  new_content.append(f'**Analysis Type:** {result.get("analysis_type", "Unknown")}\n')
  new_content.append(f'**Focus:** {result.get("focus", "comprehensive")}\n\n')

  # Add executive summary
  if 'executive_summary' in result:
    summary = result['executive_summary']
    new_content.append('## 📊 Executive Summary\n\n')
    new_content.append(f'- **Total Traces Analyzed:** {summary.get("total_traces_analyzed", 0)}\n')
    new_content.append(f'- **Critical Issues Found:** {summary.get("critical_issues_found", 0)}\n')
    new_content.append(f'- **High Priority Issues:** {summary.get("high_priority_issues", 0)}\n')
    new_content.append(f'- **Recommended Schemas:** {summary.get("recommended_schemas", 0)}\n')
    new_content.append(f'- **Suggested Sessions:** {summary.get("suggested_sessions", 0)}\n\n')

  # Add SME engagement plan
  if 'sme_engagement_plan' in result:
    plan = result['sme_engagement_plan']

    # Critical Issues
    if 'critical_issues' in plan and plan['critical_issues']:
      new_content.append('## 🚨 Critical Issues Requiring SME Attention\n\n')
      for issue in plan['critical_issues']:
        new_content.append(f'### {issue.get("title", "Unknown Issue")}\n\n')
        new_content.append(f'- **Type:** `{issue.get("issue_type", "unknown")}`\n')
        new_content.append(f'- **Severity:** {issue.get("severity", "unknown")}\n')
        new_content.append(f'- **Affected Traces:** {issue.get("affected_traces", 0)}\n')
        sme_focus = issue.get('sme_focus', {})
        if sme_focus:
          new_content.append(f'- **SME Focus:** {sme_focus.get("question", "")}\n')
        new_content.append('\n')

    # Schema Recommendations
    if 'recommended_schemas' in plan and plan['recommended_schemas']:
      new_content.append('## 📋 Recommended Labeling Schemas\n\n')
      for schema in plan['recommended_schemas']:
        new_content.append(f'### {schema.get("schema_name", "Unknown Schema")}\n\n')
        new_content.append(f'- **Type:** {schema.get("schema_type", "unknown")}\n')
        new_content.append(f'- **Priority Score:** {schema.get("priority_score", 0)}\n')
        new_content.append(f'- **Target Issue:** {schema.get("target_issue_type", "unknown")}\n')
        new_content.append(f'- **Description:** {schema.get("description", "")}\n\n')

    # Session Configurations
    if 'session_configurations' in plan and plan['session_configurations']:
      new_content.append('## 🎯 Suggested Labeling Sessions\n\n')
      for session in plan['session_configurations']:
        new_content.append(f'### {session.get("session_name", "Unknown Session")}\n\n')
        new_content.append(f'- **Type:** {session.get("session_type", "unknown")}\n')
        new_content.append(f'- **Target Issue:** {session.get("target_issue", "unknown")}\n')
        new_content.append(f'- **Trace Count:** {session.get("trace_count", 0)}\n')
        new_content.append(f'- **Severity:** {session.get("severity", "unknown")}\n\n')

  # Add the AI analysis
  if 'ai_analysis' in result:
    new_content.append('## 🧠 AI-Generated Analysis\n\n')
    new_content.append(result['ai_analysis'])
    new_content.append('\n\n')

  # Add raw SME analysis details if available
  if 'raw_sme_analysis' in result:
    sme_analysis = result['raw_sme_analysis']

    # Issue detection summary
    if 'issue_detection' in sme_analysis:
      issues_summary = sme_analysis['issue_detection'].get('summary', {})
      if issues_summary:
        new_content.append('## 📈 Issue Detection Summary\n\n')
        new_content.append(f'- **Total Traces:** {issues_summary.get("total_traces", 0)}\n')
        new_content.append(f'- **Issues Detected:** {issues_summary.get("issues_detected", 0)}\n')
        new_content.append(f'- **Critical Issues:** {issues_summary.get("critical_issues", 0)}\n')
        new_content.append(f'- **High Issues:** {issues_summary.get("high_issues", 0)}\n')
        new_content.append(f'- **Medium Issues:** {issues_summary.get("medium_issues", 0)}\n\n')

  # Convert content to single string
  markdown_content = ''.join(new_content)

  # Store the analysis as MLflow artifacts
  try:
    storage_result = artifact_manager.store_experiment_summary(
      experiment_id=experiment_id,
      summary_content=markdown_content,
      summary_data=result,
      labeling_session_run_id=session_run_id,
      tags={
        'analysis.focus': result.get('focus', 'comprehensive'),
        'analysis.model_endpoint': result.get('metadata', {}).get('model_endpoint', 'unknown'),
      },
    )

    print('✅ Analysis successfully stored to MLflow artifacts')
    print(f'   Run ID: {storage_result["run_id"]}')
    print(f'   Artifact URI: {storage_result["artifact_uri"]}')

  except Exception as e:
    print(f'❌ Failed to store analysis to MLflow: {e}')
    # Fallback to file system if MLflow storage fails
    print('   Falling back to file system storage...')
    reports_dir = Path('reports') / 'experiments'
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_file = reports_dir / f'{experiment_id}_summary.md'
    with open(summary_file, 'w') as f:
      f.write(markdown_content)
    print(f'   ✅ Analysis saved to {summary_file}')


def print_analysis_result(result: dict, format_type: str):
  """Print the analysis result in the specified format."""
  if format_type == 'json':
    print(json.dumps(result, indent=2, default=str))
    return

  # Text format - structured markdown-like output
  if result.get('status') == 'error':
    print(f'❌ Analysis Failed: {result.get("error", "Unknown error")}')
    return

  # Print AI analysis with beautiful formatting
  # The analysis content is in 'content' field, not 'ai_analysis'
  ai_analysis = result.get('content') or result.get('ai_analysis', 'No analysis generated')

  print('\n📊 AI ANALYSIS REPORT')
  print('=' * 60)

  # Print experiment metadata
  metadata = result.get('metadata', {})
  print('\n📋 **Analysis Details**:')
  print(f'   • Experiment ID: {result.get("experiment_id", "Unknown")}')
  print(
    f'   • Analysis Type: {result.get("analysis_type", "Unknown")} ({result.get("focus", "comprehensive")})'
  )
  print(f'   • Traces Analyzed: {metadata.get("traces_analyzed", 0)}')
  print(f'   • Model Endpoint: {metadata.get("model_endpoint", "Unknown")}')
  print(f'   • Sample Size: {metadata.get("traces_analyzed", metadata.get("sample_size", 0))}')

  print('\n' + '=' * 60)
  print(ai_analysis)
  print('=' * 60)

  # Print raw data summary if available
  raw_data = result.get('raw_data', {})
  if raw_data:
    experiment_info = raw_data.get('experiment_info', {})
    if experiment_info:
      print('\n📈 **Experiment Summary**:')
      print(f'   • Name: {experiment_info.get("name", "Unknown")}')
      if experiment_info.get('creation_time'):
        print(f'   • Created: {experiment_info.get("creation_time")}')
      if experiment_info.get('last_update_time'):
        print(f'   • Last Updated: {experiment_info.get("last_update_time")}')


def print_session_analysis_result(result: dict, format_type: str):
  """Print the session analysis result in the specified format."""
  if format_type == 'json':
    print(json.dumps(result, indent=2, default=str))
    return

  # Text format - structured output
  if result.get('status') == 'error':
    print(f'❌ Session Analysis Failed: {result.get("error", "Unknown error")}')
    return

  ai_analysis = result.get('ai_analysis', 'No analysis generated')

  print('\n👥 SME LABELING SESSION ANALYSIS')
  print('=' * 60)

  # Print session metadata
  metadata = result.get('metadata', {})
  print('\n📋 **Session Details**:')
  print(f'   • Session ID: {result.get("session_id", "Unknown")}')
  print(f'   • Analysis Type: {result.get("session_analysis_type", "Unknown")}')
  print(f'   • Completion Rate: {metadata.get("completion_rate", 0):.1f}%')
  print(f'   • Total Items: {metadata.get("total_items", 0)}')
  print(f'   • Completed Items: {metadata.get("completed_items", 0)}')
  print(f'   • Schemas: {metadata.get("schemas_count", 0)}')
  print(f'   • Model Endpoint: {metadata.get("model_endpoint", "Unknown")}')

  print('\n' + '=' * 60)
  print(ai_analysis)
  print('=' * 60)


async def main():
  """Main function for AI-powered experiment analysis."""
  parser = argparse.ArgumentParser(
    description='Generate AI-powered analysis of MLflow experiments and labeling sessions',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Comprehensive SME engagement analysis (stores to MLflow artifacts)
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602
  
  # Analyze with larger trace sample for deeper insights
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602 --trace-sample-size 100
  
  # Analyze without storing to MLflow artifacts  
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602 --no-write
  
  # Store analysis to specific labeling session run
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602 --session-run-id abc123def456
  
  # Analyze labeling session
  python tools/ai_analyze_experiment.py --session --review-app-id abc123 --session-id def456
  
  # Custom model endpoint
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602 --model-endpoint my-endpoint
  
  # JSON output for further processing
  python tools/ai_analyze_experiment.py --experiment-id 2178582188830602 --format json

Focus Areas:
  - comprehensive: Complete SME engagement analysis with issue detection, schema recommendations, 
                   session curation, and ROI analysis (default)
  - sme-engagement: Focused on SME engagement strategy and labeling optimization
  - patterns: Focus on execution patterns and behavioral trends
  - performance: Emphasize performance metrics and optimization opportunities
  - quality: Concentrate on response quality and effectiveness indicators

Session Analysis Types:
  - sme_insights: Focus on SME behavior and feedback patterns
  - quality_patterns: Analyze assessment quality and consistency
  - completion_analysis: Study completion rates and engagement factors
        """,
  )

  # Analysis target options
  target_group = parser.add_mutually_exclusive_group(required=True)
  target_group.add_argument('--experiment-id', help='MLflow experiment ID to analyze')
  target_group.add_argument('--experiment-name', help='MLflow experiment name to analyze')
  target_group.add_argument(
    '--session', action='store_true', help='Analyze a labeling session instead of experiment'
  )

  # Experiment analysis options
  parser.add_argument(
    '--focus',
    choices=['comprehensive', 'sme-engagement', 'patterns', 'performance', 'quality'],
    default='comprehensive',
    help='Focus area for experiment analysis (default: comprehensive SME engagement)',
  )

  parser.add_argument(
    '--trace-sample-size',
    type=int,
    default=50,
    help='Number of traces to analyze in detail for comprehensive SME analysis (default: 50)',
  )

  parser.add_argument(
    '--no-write',
    action='store_true',
    help='Do not store analysis to MLflow artifacts',
  )

  parser.add_argument(
    '--session-run-id',
    help='Use specific labeling session run ID for storing artifacts',
  )

  # Session analysis options
  parser.add_argument('--review-app-id', help='Review app ID (required for session analysis)')

  parser.add_argument('--session-id', help='Labeling session ID (required for session analysis)')

  parser.add_argument(
    '--session-analysis-type',
    choices=['sme_insights', 'quality_patterns', 'completion_analysis'],
    default='sme_insights',
    help='Type of session analysis (default: sme_insights)',
  )

  # General options
  parser.add_argument(
    '--model-endpoint',
    default=None,
    help='Model serving endpoint to use (default: from MODEL_ENDPOINT env var)',
  )

  parser.add_argument(
    '--format', choices=['text', 'json'], default='text', help='Output format (default: text)'
  )

  parser.add_argument('--debug', action='store_true', help='Enable debug logging')

  args = parser.parse_args()

  # Set up logging
  import logging

  level = logging.DEBUG if args.debug else logging.INFO
  logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

  print_banner()

  try:
    # Initialize AI analyzer with config fallback
    model_endpoint = args.model_endpoint or config.model_endpoint
    analyzer = AIExperimentAnalyzer(model_endpoint)

    if args.session:
      # Session analysis
      if not args.review_app_id or not args.session_id:
        print('❌ Error: --review-app-id and --session-id are required for session analysis')
        sys.exit(1)

      print(f'🔄 Analyzing labeling session {args.session_id}...')
      print(f'📊 Analysis type: {args.session_analysis_type}')
      print(f'🤖 Using model: {model_endpoint}')
      print()

      result = await analyzer.analyze_labeling_session(
        review_app_id=args.review_app_id,
        session_id=args.session_id,
        analysis_type=args.session_analysis_type,
      )

      print_session_analysis_result(result, args.format)

    else:
      # Experiment analysis
      experiment_id = args.experiment_id

      # Handle experiment name lookup
      if args.experiment_name:
        try:
          # For now, we don't support experiment name lookup
          print(
            '❌ Error: Experiment name lookup not currently supported. Please use --experiment-id instead.'
          )
          sys.exit(1)
        except Exception as e:
          print(f"❌ Error finding experiment '{args.experiment_name}': {e}")
          sys.exit(1)

      print(f'🔄 Analyzing experiment {experiment_id}...')
      print(f'🎯 Focus: {args.focus}')
      print(f'📈 Sample size: {args.trace_sample_size} traces')
      print(f'🤖 Using model: {model_endpoint}')
      print()

      result = await analyzer.analyze_experiment(
        experiment_id=experiment_id,
        analysis_focus=args.focus,
        trace_sample_size=args.trace_sample_size,
      )

      print_analysis_result(result, args.format)

      # Write to MLflow artifacts unless disabled
      if result.get('status') == 'success' and not args.no_write:
        write_to_mlflow_artifacts(experiment_id, result, session_run_id=args.session_run_id)

    if result.get('status') == 'success':
      print('\n✅ AI analysis completed successfully!')
    else:
      print(f'\n❌ Analysis failed: {result.get("error", "Unknown error")}')
      sys.exit(1)

  except KeyboardInterrupt:
    print('\n⚠️ Analysis interrupted by user')
    sys.exit(1)
  except Exception as e:
    print(f'\n❌ Unexpected error: {e}')
    if args.debug:
      import traceback

      traceback.print_exc()
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
