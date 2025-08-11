#!/usr/bin/env python3
"""Search for traces in MLflow experiments."""

import argparse
import json
import sys

from server.utils.config import config
from server.utils.mlflow_utils import _extract_request_response_preview, search_traces


def _convert_traces_to_json_format(traces, include_spans: bool = False):
  """Convert raw MLflow Trace objects to JSON format."""
  trace_list = []

  for trace in traces:
    try:
      # Extract request/response previews
      request_preview, response_preview = _extract_request_response_preview(trace)

      # Convert trace info
      trace_info = {
        'trace_id': trace.info.trace_id,
        'trace_location': {
          'experiment_id': trace.info.experiment_id,
          'run_id': trace.info.run_id
          if hasattr(trace.info, 'run_id') and trace.info.run_id
          else '',
        },
        'request_time': str(trace.info.timestamp_ms),
        'execution_duration': f'{trace.info.execution_time_ms}ms'
        if trace.info.execution_time_ms
        else '0ms',
        'state': trace.info.status or 'OK',
        'trace_metadata': dict(trace.info.request_metadata) if trace.info.request_metadata else {},
        'tags': dict(trace.info.tags) if trace.info.tags else {},
        'assessments': [],
        'request_preview': request_preview,
        'response_preview': response_preview,
      }

      # Convert trace data with spans (only if requested)
      trace_data = {'spans': []}
      if include_spans and trace.data and trace.data.spans is not None:
        for span in trace.data.spans:
          span_dict = {
            'name': span.name,
            'span_id': span.span_id,
            'parent_id': span.parent_id,
            'start_time_ms': int(span.start_time_ns // 1_000_000) if span.start_time_ns else 0,
            'end_time_ms': int(span.end_time_ns // 1_000_000) if span.end_time_ns else 0,
            'status': {
              'status_code': 'OK' if span.status == 'OK' or not span.status else 'ERROR',
              'description': span.status_message
              if hasattr(span, 'status_message') and span.status_message
              else '',
            },
            'span_type': getattr(span, 'span_type', 'UNKNOWN'),
            'inputs': getattr(span, 'inputs', None),
            'outputs': getattr(span, 'outputs', None),
            'attributes': getattr(span, 'attributes', None),
          }
          trace_data['spans'].append(span_dict)

      # Convert assessments if present
      if hasattr(trace.info, 'assessments') and trace.info.assessments is not None:
        for assessment in trace.info.assessments:
          assessment_dict = {}

          if hasattr(assessment, 'name'):
            assessment_dict['name'] = assessment.name

          assessment_value = None
          if hasattr(assessment, 'feedback') and assessment.feedback:
            if hasattr(assessment.feedback, 'value'):
              assessment_value = assessment.feedback.value
          elif hasattr(assessment, 'expectation') and assessment.expectation:
            if hasattr(assessment.expectation, 'value'):
              assessment_value = assessment.expectation.value
          elif hasattr(assessment, 'value'):
            assessment_value = assessment.value

          if assessment_value is None:
            continue

          assessment_dict['value'] = assessment_value

          if hasattr(assessment, 'metadata') and assessment.metadata:
            assessment_dict['metadata'] = assessment.metadata

          if hasattr(assessment, 'source') and assessment.source:
            if hasattr(assessment.source, 'source_type') and hasattr(
              assessment.source, 'source_id'
            ):
              assessment_dict['source'] = (
                f'{assessment.source.source_type}:{assessment.source.source_id}'
              )
            else:
              assessment_dict['source'] = str(assessment.source)

          if 'name' in assessment_dict:
            trace_info['assessments'].append(assessment_dict)

      trace_list.append({'info': trace_info, 'data': trace_data})
    except Exception:
      continue  # Skip traces that can't be converted

  return {
    'traces': trace_list,
    'next_page_token': None,
  }


def main():
  """Search for traces in MLflow experiments with comprehensive filtering."""
  description = """
Search for traces in MLflow experiments using SQL-like query syntax.

SEARCH ATTRIBUTES:
  - request_id, timestamp_ms, execution_time_ms, status, name, run_id

FILTER SYNTAX:
  - Numeric: >, >=, =, !=, <, <= (e.g., "execution_time_ms > 1000")
  - String: =, !=, IN, NOT IN (e.g., "status = 'OK'")
  - Tags: tags.key or tag.key (e.g., "tags.model_name = 'gpt-4'")
  - Metadata: metadata.key (e.g., "metadata.user = 'john'")

STATUS VALUES: 'OK', 'ERROR', 'IN_PROGRESS'
ORDER BY: timestamp_ms, execution_time_ms (add DESC for descending)

EXAMPLES:
  # Recent traces (default experiment)
  search_traces.py --limit 10 --order-by "timestamp_ms DESC"

  # Performance analysis
  search_traces.py --filter "status = 'OK' AND execution_time_ms > 5000"

  # Error investigation
  search_traces.py --filter "status = 'ERROR'" --order-by "timestamp_ms DESC"

  # Tag-based search
  search_traces.py --filter "tags.model_name = 'claude-3'"

  # Time range (last hour)
  search_traces.py --filter "timestamp_ms > $(date -d '1 hour ago' +%s)000"

  # Specific experiment
  search_traces.py 123456789 --filter "execution_time_ms > 1000"
"""

  parser = argparse.ArgumentParser(
    description=description, formatter_class=argparse.RawDescriptionHelpFormatter
  )
  parser.add_argument(
    'experiment_ids',
    nargs='*',
    help='Experiment IDs to search in (defaults to config experiment_id)',
  )
  parser.add_argument(
    '--filter', dest='filter_string', help='SQL-like filter string (see examples above)'
  )
  parser.add_argument('--run-id', help='Run ID to filter by')
  parser.add_argument(
    '--limit',
    type=int,
    default=1000,
    help='Maximum number of traces to return (default: 1000)',
  )
  parser.add_argument(
    '--order-by',
    nargs='+',
    help='Sort fields: timestamp_ms, execution_time_ms (add DESC for descending)',
  )
  parser.add_argument('--page-token', help='Pagination token for retrieving next page of results')
  parser.add_argument(
    '--include-spans',
    action='store_true',
    help='Include detailed span data in results',
  )

  args = parser.parse_args()

  try:
    # Use config experiment_id if no experiment_ids provided
    experiment_ids = args.experiment_ids if args.experiment_ids else [config.experiment_id]
    kwargs = {'experiment_ids': experiment_ids}

    if args.filter_string:
      kwargs['filter_string'] = args.filter_string
    if args.run_id:
      kwargs['run_id'] = args.run_id
    if args.limit:
      kwargs['max_results'] = args.limit
    if args.order_by:
      kwargs['order_by'] = args.order_by
    if args.page_token:
      kwargs['page_token'] = args.page_token
    if args.include_spans:
      kwargs['include_spans'] = args.include_spans

    # Get raw traces and convert to JSON format
    raw_traces = search_traces(
      experiment_ids=kwargs.get('experiment_ids'),
      filter_string=kwargs.get('filter_string'),
      run_id=kwargs.get('run_id'),
      max_results=kwargs.get('max_results'),
      order_by=kwargs.get('order_by'),
    )

    # Convert to the expected JSON format
    result = _convert_traces_to_json_format(raw_traces, kwargs.get('include_spans', False))
    print(json.dumps(result, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
