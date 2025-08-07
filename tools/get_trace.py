#!/usr/bin/env python3
"""Get a specific trace by ID."""

import argparse
import inspect
import json
import sys

from dotenv import load_dotenv

from server.utils.mlflow_utils import _extract_request_response_preview, get_trace

# Load environment variables
load_dotenv()
load_dotenv('.env.local')


def _convert_trace_to_json_format(trace):
  """Convert raw MLflow Trace object to JSON format."""
  # Extract request/response previews
  request_preview, response_preview = _extract_request_response_preview(trace)

  # Convert trace info
  trace_info = {
    'trace_id': trace.info.trace_id,
    'experiment_id': trace.info.experiment_id,
    'request_time': str(trace.info.timestamp_ms),
    'execution_duration': f'{trace.info.execution_time_ms}ms'
    if trace.info.execution_time_ms
    else '0ms',
    'state': trace.info.status or 'OK',
    'request_id': trace.info.trace_id,  # Use trace_id as request_id for compatibility
    'assessments': [],
    'request_preview': request_preview,
    'response_preview': response_preview,
  }

  # Convert spans data if available
  spans_data = []
  if trace.data and trace.data.spans:
    for span in trace.data.spans:
      span_dict = {
        'span_id': span.span_id,
        'name': span.name,
        'start_time_ms': int(span.start_time_ns // 1_000_000) if span.start_time_ns else 0,
        'end_time_ms': int(span.end_time_ns // 1_000_000) if span.end_time_ns else 0,
        'parent_id': span.parent_id,
        'attributes': dict(span.attributes) if span.attributes else {},
        'inputs': getattr(span, 'inputs', None),
        'outputs': getattr(span, 'outputs', None),
        'span_type': getattr(
          span,
          'span_type',
          span.attributes.get('mlflow.spanType', 'UNKNOWN') if span.attributes else 'UNKNOWN',
        ),
        'status': {
          'status_code': 'OK'
          if not hasattr(span, 'status') or span.status == 'OK' or not span.status
          else 'ERROR',
          'description': getattr(span, 'status_message', '')
          if hasattr(span, 'status_message')
          else '',
        },
      }
      spans_data.append(span_dict)

  # Convert assessments if present
  if hasattr(trace.info, 'assessments') and trace.info.assessments:
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

      if assessment_value is not None:
        assessment_dict['value'] = assessment_value

        if hasattr(assessment, 'metadata') and assessment.metadata:
          assessment_dict['metadata'] = assessment.metadata

        if hasattr(assessment, 'source') and assessment.source:
          if hasattr(assessment.source, 'source_type') and hasattr(assessment.source, 'source_id'):
            assessment_dict['source'] = (
              f'{assessment.source.source_type}:{assessment.source.source_id}'
            )
          else:
            assessment_dict['source'] = str(assessment.source)

        if 'name' in assessment_dict:
          trace_info['assessments'].append(assessment_dict)

  return {
    'info': trace_info,
    'data': {'spans': spans_data},
  }


def main():
  """Get a specific trace."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(get_trace)
  description = func_doc.split('\n')[0] if func_doc else 'Get a specific trace by ID'

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('trace_id', help='Trace ID to retrieve')

  args = parser.parse_args()

  try:
    # Get raw trace and convert to JSON format
    raw_trace = get_trace(trace_id=args.trace_id)
    result = _convert_trace_to_json_format(raw_trace)
    print(json.dumps(result, indent=2, default=str))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
