#!/usr/bin/env python3
"""Analyze patterns in recent MLflow traces to understand agent architecture and workflows."""

import argparse
import json
import sys

from server.utils.trace_analysis import analyze_trace_patterns


def main():
  """Analyze trace patterns in MLflow experiments."""
  description = """
Analyze patterns in recent MLflow traces to understand agent architecture and data flows.

This tool examines the structure of traces to identify:
- Span types and hierarchy patterns
- Tool usage and calling patterns
- Conversation flow and message formats
- Input/output data structures
- Agent workflow patterns (RAG, function calling, etc.)

EXAMPLES:
  # Analyze last 10 traces from config experiment
  analyze_trace_patterns.py

  # Analyze last 20 traces from specific experiment
  analyze_trace_patterns.py --experiment-id 123456789 --limit 20

  # Quick analysis of last 5 traces
  analyze_trace_patterns.py --limit 5
"""

  parser = argparse.ArgumentParser(
    description=description, formatter_class=argparse.RawDescriptionHelpFormatter
  )
  parser.add_argument(
    '--experiment-id',
    help='Experiment ID to analyze (defaults to config experiment_id)',
  )
  parser.add_argument(
    '--limit',
    type=int,
    default=10,
    help='Number of recent traces to analyze (default: 10)',
  )

  args = parser.parse_args()

  try:
    result = analyze_trace_patterns(experiment_id=args.experiment_id, limit=args.limit)
    print(json.dumps(result, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
