"""Trace pattern analysis utility for understanding agent workflows and data structures."""

import logging
from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional

from server.utils.config import get_config
from server.utils.mlflow_utils import search_traces

logger = logging.getLogger(__name__)


def analyze_trace_patterns(experiment_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
  """Analyze patterns in recent traces to understand agent architecture and data flows.

  Args:
      experiment_id: Experiment ID to analyze (defaults to config experiment_id)
      limit: Number of recent traces to analyze

  Returns:
      Dictionary containing structured analysis of trace patterns
  """
  # Use config experiment_id if not provided
  if not experiment_id:
    config = get_config()
    experiment_id = config.get('experiment_id')
    if not experiment_id:
      raise ValueError('No experiment_id provided and none found in config')

  logger.info(f'Starting trace pattern analysis for experiment {experiment_id}, limit {limit}')

  # Fetch recent traces
  raw_traces = search_traces(
    experiment_ids=[experiment_id],
    max_results=limit,
    order_by=['timestamp_ms DESC'],
  )

  # Convert MLflow Trace objects to dictionary format expected by analysis functions
  traces = []
  if raw_traces:
    for trace in raw_traces:
      try:
        trace_dict = {
          'info': {
            'trace_id': trace.info.trace_id,
            'experiment_id': trace.info.experiment_id,
            'timestamp_ms': trace.info.timestamp_ms,
            'execution_time_ms': trace.info.execution_time_ms,
            'status': trace.info.status,
          },
          'data': {
            'request': getattr(trace.data, 'request', None),
            'response': getattr(trace.data, 'response', None),
            'spans': [],
          },
        }

        # Convert spans if they exist
        if trace.data and trace.data.spans:
          for span in trace.data.spans:
            span_dict = {
              'span_id': span.span_id,
              'parent_id': getattr(span, 'parent_id', None),
              'span_type': span.span_type,
              'name': span.name,
              'start_time_ms': span.start_time_ms,
              'end_time_ms': span.end_time_ms,
              'inputs': span.inputs or {},
              'outputs': span.outputs or {},
              'attributes': getattr(span, 'attributes', {}),
            }
            trace_dict['data']['spans'].append(span_dict)

        traces.append(trace_dict)
      except Exception as e:
        logger.warning(f'Error converting trace: {e}')
        continue

  total_traces = len(traces)

  if total_traces == 0:
    return {
      'analysis_summary': {
        'total_traces': 0,
        'conversation_type': 'unknown',
        'agent_pattern': 'unknown',
      },
      'span_patterns': {},
      'tool_usage': {},
      'input_output_patterns': {},
      'conversation_flow': {},
    }

  logger.info(f'Analyzing {total_traces} traces')

  # Initialize analysis counters
  span_types = Counter()
  span_names = Counter()
  hierarchy_depths = []
  tools_detected = set()
  tool_parameters = defaultdict(set)
  conversation_lengths = []
  user_message_lengths = []
  response_lengths = []
  input_formats = Counter()
  output_formats = Counter()

  # Analyze each trace
  for trace in traces:
    spans = trace.get('data', {}).get('spans', [])

    if not spans:
      continue

    # Calculate hierarchy depth
    hierarchy_depths.append(len(spans))

    # Analyze spans
    for span in spans:
      span_type = span.get('span_type', 'UNKNOWN')
      span_name = span.get('name', 'unknown')

      span_types[span_type] += 1
      span_names[span_name] += 1

      # Analyze tool usage
      if span_type == 'TOOL':
        tools_detected.add(span_name)

        # Extract tool parameters from inputs
        inputs = span.get('inputs', {})
        if inputs and isinstance(inputs, dict):
          for param_key in inputs.keys():
            tool_parameters[span_name].add(param_key)

      # Analyze conversation patterns from CHAT_MODEL spans
      elif span_type in ['CHAT_MODEL', 'LLM']:
        inputs = span.get('inputs', {})
        outputs = span.get('outputs', {})

        # Analyze input format
        if inputs:
          if 'messages' in inputs:
            input_formats['chat_messages'] += 1
            messages = inputs.get('messages', [])
            if isinstance(messages, list):
              conversation_lengths.append(len(messages))
              # Analyze user message lengths
              for msg in messages:
                if isinstance(msg, dict) and msg.get('role') == 'user':
                  content = msg.get('content', '')
                  if content:
                    user_message_lengths.append(len(str(content)))
          elif 'prompt' in inputs:
            input_formats['prompt'] += 1
            prompt = inputs.get('prompt', '')
            if prompt:
              user_message_lengths.append(len(str(prompt)))
          else:
            input_formats['structured'] += 1

        # Analyze output format
        if outputs:
          if 'choices' in outputs:
            output_formats['choices_format'] += 1
            choices = outputs.get('choices', [])
            if isinstance(choices, list) and choices:
              choice = choices[0]
              if isinstance(choice, dict) and 'message' in choice:
                content = choice['message'].get('content', '')
                if content:
                  response_lengths.append(len(str(content)))
          elif 'generations' in outputs:
            output_formats['generations_format'] += 1
          elif 'text' in outputs:
            output_formats['text_format'] += 1
            text = outputs.get('text', '')
            if text:
              response_lengths.append(len(str(text)))
          else:
            output_formats['structured'] += 1

  # Determine conversation type and agent pattern
  conversation_type = _determine_conversation_type(span_types, input_formats)
  agent_pattern = _determine_agent_pattern(span_types, tools_detected)
  tool_calling_pattern = _determine_tool_calling_pattern(traces)

  # Calculate statistics
  hierarchy_stats = {
    'avg': round(mean(hierarchy_depths), 1) if hierarchy_depths else 0,
    'max': max(hierarchy_depths) if hierarchy_depths else 0,
  }

  conversation_stats = {
    'avg_turns': round(mean(conversation_lengths), 1) if conversation_lengths else 0,
    'user_message_length': {
      'avg': round(mean(user_message_lengths)) if user_message_lengths else 0,
      'max': max(user_message_lengths) if user_message_lengths else 0,
    },
    'response_length': {
      'avg': round(mean(response_lengths)) if response_lengths else 0,
      'max': max(response_lengths) if response_lengths else 0,
    },
  }

  # Convert tool parameters to regular dict
  tool_params_dict = {tool: list(params) for tool, params in tool_parameters.items()}

  return {
    'analysis_summary': {
      'total_traces': total_traces,
      'conversation_type': conversation_type,
      'agent_pattern': agent_pattern,
    },
    'span_patterns': {
      'types': dict(span_types.most_common()),
      'common_names': [name for name, _ in span_names.most_common(10)],
      'hierarchy_depth': hierarchy_stats,
    },
    'tool_usage': {
      'tools_detected': list(tools_detected),
      'calling_pattern': tool_calling_pattern,
      'tool_parameters': tool_params_dict,
    },
    'input_output_patterns': {
      'input_format': dict(input_formats.most_common()),
      'output_format': dict(output_formats.most_common()),
      'common_fields': _extract_common_fields(traces),
    },
    'conversation_flow': conversation_stats,
  }


def _determine_conversation_type(span_types: Counter, input_formats: Counter) -> str:
  """Determine the type of conversation based on span types and input formats."""
  has_chat = span_types.get('CHAT_MODEL', 0) > 0 or span_types.get('LLM', 0) > 0
  has_tools = span_types.get('TOOL', 0) > 0
  uses_messages = input_formats.get('chat_messages', 0) > 0

  if has_chat and has_tools and uses_messages:
    return 'multi_turn_chat_with_tools'
  elif has_chat and uses_messages:
    return 'multi_turn_chat'
  elif has_chat and has_tools:
    return 'single_turn_with_tools'
  elif has_chat:
    return 'single_turn_chat'
  else:
    return 'structured_processing'


def _determine_agent_pattern(span_types: Counter, tools_detected: set) -> str:
  """Determine the agent pattern based on span types and tools."""
  has_retriever = span_types.get('RETRIEVER', 0) > 0
  has_tools = span_types.get('TOOL', 0) > 0
  has_agent = span_types.get('AGENT', 0) > 0
  has_chain = span_types.get('CHAIN', 0) > 0

  # Check for common tool patterns
  search_tools = any(
    'search' in tool.lower() or 'retriev' in tool.lower() for tool in tools_detected
  )

  if has_retriever or search_tools:
    if has_tools and len(tools_detected) > 1:
      return 'rag_with_function_calling'
    else:
      return 'rag_pattern'
  elif has_agent and has_tools:
    return 'multi_agent_with_tools'
  elif has_tools and len(tools_detected) > 2:
    return 'function_calling_agent'
  elif has_chain:
    return 'chain_processing'
  elif has_agent:
    return 'simple_agent'
  else:
    return 'direct_generation'


def _determine_tool_calling_pattern(traces: List[Dict[str, Any]]) -> str:
  """Analyze tool calling patterns across traces."""
  parallel_calls = 0
  sequential_calls = 0
  nested_calls = 0

  for trace in traces:
    spans = trace.get('data', {}).get('spans', [])
    tool_spans = [s for s in spans if s.get('span_type') == 'TOOL']

    if len(tool_spans) <= 1:
      continue

    # Check for parallel calls (overlapping time ranges)
    for i, span1 in enumerate(tool_spans):
      for span2 in tool_spans[i + 1 :]:
        start1 = span1.get('start_time_ms', 0)
        end1 = span1.get('end_time_ms', 0)
        start2 = span2.get('start_time_ms', 0)
        end2 = span2.get('end_time_ms', 0)

        if start1 < end2 and start2 < end1:  # Overlapping
          parallel_calls += 1
          break

    # Check for nested calls (parent-child relationships)
    for span in tool_spans:
      if span.get('parent_id') in [s.get('span_id') for s in tool_spans]:
        nested_calls += 1

    # Otherwise assume sequential
    if len(tool_spans) > 1 and parallel_calls == 0 and nested_calls == 0:
      sequential_calls += 1

  if parallel_calls > sequential_calls and parallel_calls > nested_calls:
    return 'parallel_execution'
  elif nested_calls > 0:
    return 'nested_with_dependencies'
  else:
    return 'sequential'


def _extract_common_fields(traces: List[Dict[str, Any]]) -> List[str]:
  """Extract commonly used field names across traces."""
  field_counter = Counter()

  for trace in traces:
    spans = trace.get('data', {}).get('spans', [])

    for span in spans:
      # Count fields in inputs
      inputs = span.get('inputs', {})
      if isinstance(inputs, dict):
        field_counter.update(inputs.keys())

      # Count fields in outputs
      outputs = span.get('outputs', {})
      if isinstance(outputs, dict):
        field_counter.update(outputs.keys())

      # Count fields in attributes
      attributes = span.get('attributes', {})
      if isinstance(attributes, dict):
        field_counter.update(attributes.keys())

  # Return top 10 most common fields
  return [field for field, _ in field_counter.most_common(10)]
