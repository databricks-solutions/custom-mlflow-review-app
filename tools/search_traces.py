#!/usr/bin/env python3
"""Search for traces in MLflow experiments."""

import argparse
import json
import sys

from server.utils.config import config
from server.utils.mlflow_utils import _extract_request_response_preview, search_traces


def _convert_traces_to_json_format(traces, include_spans: bool = False):
  """Convert raw MLflow Trace objects to JSON format using built-in to_dict()."""
  trace_list = []

  for trace in traces:
    try:
      # Use built-in to_dict() for full trace serialization
      trace_dict = trace.to_dict()

      # Extract request/response previews
      request_preview, response_preview = _extract_request_response_preview(trace)

      # Transform the dict to match expected format
      trace_info_dict = trace_dict.get('info', {})

      # Convert trace info
      trace_info = {
        'trace_id': trace_info_dict.get('trace_id', trace_info_dict.get('request_id', '')),
        'trace_location': {
          'experiment_id': trace_info_dict.get('experiment_id', ''),
          'run_id': trace_info_dict.get('run_id', ''),
        },
        'request_time': str(trace_info_dict.get('timestamp_ms', '')),
        'execution_duration': f'{trace_info_dict.get("execution_time_ms", 0)}ms',
        'state': trace_info_dict.get('status', 'OK'),
        'trace_metadata': trace_info_dict.get('request_metadata', {}),
        'tags': trace_info_dict.get('tags', {}),
        'assessments': [],
        'request_preview': request_preview,
        'response_preview': response_preview,
      }

      # Convert trace data with spans (only if requested)
      trace_data_dict = trace_dict.get('data', {})
      trace_data = {'spans': []}

      if include_spans and trace_data_dict.get('spans'):
        for span_dict in trace_data_dict['spans']:
          converted_span = {
            'name': span_dict.get('name', ''),
            'span_id': span_dict.get('span_id', ''),
            'parent_id': span_dict.get('parent_id'),
            'start_time_ms': int(span_dict.get('start_time_ns', 0) // 1_000_000),
            'end_time_ms': int(span_dict.get('end_time_ns', 0) // 1_000_000),
            'status': {
              'status_code': span_dict.get('status', 'OK'),
              'description': span_dict.get('status_message', ''),
            },
            'span_type': span_dict.get(
              'span_type', span_dict.get('attributes', {}).get('mlflow.spanType', 'UNKNOWN')
            ),
            'inputs': span_dict.get('inputs'),
            'outputs': span_dict.get('outputs'),
            'attributes': span_dict.get('attributes'),
          }
          trace_data['spans'].append(converted_span)

      # Convert assessments if present - use built-in to_dictionary() method
      if hasattr(trace.info, 'assessments') and trace.info.assessments is not None:
        for assessment in trace.info.assessments:
          try:
            # Use the built-in to_dictionary() method which includes rationale
            assessment_dict = assessment.to_dictionary()

            # Simplify the structure for consistency with existing format
            simplified = {
              'name': assessment_dict.get('assessment_name', ''),
              'value': None,
              'assessment_id': assessment_dict.get('assessment_id'),
            }

            # Extract value from feedback or expectation
            if 'feedback' in assessment_dict and assessment_dict['feedback']:
              simplified['value'] = assessment_dict['feedback'].get('value')
            elif 'expectation' in assessment_dict and assessment_dict['expectation']:
              simplified['value'] = assessment_dict['expectation'].get('value')

            # Include rationale if present
            if assessment_dict.get('rationale'):
              simplified['rationale'] = assessment_dict['rationale']

            # Include metadata if present
            if assessment_dict.get('metadata'):
              simplified['metadata'] = assessment_dict['metadata']

            # Format source for consistency
            if assessment_dict.get('source'):
              source = assessment_dict['source']
              if isinstance(source, dict):
                simplified['source'] = (
                  f"{source.get('source_type', '')}:{source.get('source_id', '')}"
                )
              else:
                simplified['source'] = str(source)

            if simplified['name'] and simplified['value'] is not None:
              trace_info['assessments'].append(simplified)
          except Exception:
            # Fall back to manual extraction if to_dictionary fails
            continue

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
