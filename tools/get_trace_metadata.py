#!/usr/bin/env python3
"""Get trace metadata (info and spans without inputs/outputs) by trace ID."""

import argparse
import asyncio
import json

from server.utils.mlflow_utils import get_trace


async def main():
  """Get trace metadata by trace ID."""
  parser = argparse.ArgumentParser(
    description='Get trace metadata (info and spans without inputs/outputs) by trace ID.'
  )
  parser.add_argument('trace_id', help='Trace ID to retrieve metadata for')

  args = parser.parse_args()

  try:
    # Get the raw trace
    raw_trace = get_trace(args.trace_id)

    # Extract basic info
    trace_info = {
      'trace_id': raw_trace.info.trace_id,
      'experiment_id': raw_trace.info.experiment_id,
      'request_time': str(raw_trace.info.timestamp_ms),
      'execution_duration': f'{raw_trace.info.execution_time_ms}ms'
      if raw_trace.info.execution_time_ms
      else '0ms',
      'state': raw_trace.info.status or 'OK',
    }

    # Extract metadata (remove heavy inputs/outputs from spans)
    metadata = {'info': trace_info, 'spans': []}

    # Process spans to keep only name and type
    if raw_trace.data and raw_trace.data.spans:
      for span in raw_trace.data.spans:
        span_metadata = {
          'name': span.name,
          'type': getattr(
            span,
            'span_type',
            span.attributes.get('mlflow.spanType', 'UNKNOWN') if span.attributes else 'UNKNOWN',
          ),
        }
        metadata['spans'].append(span_metadata)

    print(json.dumps(metadata, indent=2))

  except Exception as e:
    print(f'Error: {e}')
    return 1

  return 0


if __name__ == '__main__':
  exit(asyncio.run(main()))
