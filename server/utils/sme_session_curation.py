"""SME Session Curation Utility

This module creates targeted labeling sessions by curating specific traces that will
provide the most valuable SME feedback for identified issues.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SMESessionCurator:
  """Curates targeted labeling sessions for maximum SME feedback impact."""

  def __init__(self):
    self.logger = logging.getLogger(__name__)

  def create_curated_sessions(
    self,
    traces: List[Dict[str, Any]],
    detected_issues: List[Dict[str, Any]],
    schema_recommendations: List[Dict[str, Any]],
  ) -> List[Dict[str, Any]]:
    """Group traces by quality issues for focused evaluation.

    Args:
        traces: All available traces
        detected_issues: Quality issues detected with trace examples
        schema_recommendations: Recommended schemas grounded in issues

    Returns:
        List of trace groupings organized by quality issue type
    """
    if not traces or not detected_issues:
      return self._create_baseline_quality_session(traces, schema_recommendations)

    self.logger.info(
      f'Grouping {len(traces)} traces by {len(detected_issues)} quality issues for evaluation'
    )

    sessions = []

    # Create a session for each quality issue with its example traces
    for issue in detected_issues:
      session = self._create_quality_focused_session(issue, schema_recommendations)
      if session:
        sessions.append(session)

    # Add a mixed quality assessment session if we have diverse issues
    if len(detected_issues) >= 3:
      mixed_session = self._create_mixed_quality_session(detected_issues, schema_recommendations)
      if mixed_session:
        sessions.append(mixed_session)

    return sessions

  def _has_performance_variance(self, traces: List[Dict[str, Any]]) -> bool:
    """Check if traces have significant performance variance."""
    if len(traces) < 3:
      return False

    exec_times = [t.get('info', {}).get('execution_time_ms', 0) for t in traces]
    exec_times = [t for t in exec_times if t > 0]  # Filter out zeros

    if len(exec_times) < 3:
      return False

    import statistics

    mean_time = statistics.mean(exec_times)
    std_time = statistics.stdev(exec_times) if len(exec_times) > 1 else 0

    # Significant variance if CV > 0.5
    return (std_time / mean_time) > 0.5 if mean_time > 0 else False

  def _create_quality_focused_session(
    self,
    issue: Dict[str, Any],
    schema_recommendations: List[Dict[str, Any]],
  ) -> Optional[Dict[str, Any]]:
    """Create a session focused on a specific quality issue."""
    issue_type = issue.get('issue_type', 'unknown')
    issue_title = issue.get('title', 'Unknown Issue')
    severity = issue.get('severity', 'medium')
    example_traces = issue.get('example_traces', [])
    problem_snippets = issue.get('problem_snippets', [])

    if not example_traces:
      return None

    # Find schemas that address this issue
    relevant_schemas = [
      schema
      for schema in schema_recommendations
      if schema.get('target_issue_type') == issue_type
      or issue_type in schema.get('grounded_in_traces', [])
    ]

    # Fallback to quality schemas if none match
    if not relevant_schemas:
      relevant_schemas = [
        schema
        for schema in schema_recommendations
        if 'quality' in schema.get('key', '').lower()
        or 'correctness' in schema.get('key', '').lower()
      ][:2]

    session_name = f'{issue_title} Evaluation'

    return {
      'session_name': session_name,
      'issue_type': issue_type,
      'issue_description': issue_title,
      'severity': severity,
      'traces_with_issue': [
        {
          'trace_id': trace_id,
          'problem_example': problem_snippets[i]
          if i < len(problem_snippets)
          else 'Quality issue detected',
        }
        for i, trace_id in enumerate(example_traces[:15])  # Limit to 15 traces
      ],
      'trace_count': len(example_traces[:15]),
      'recommended_schemas': [schema['key'] for schema in relevant_schemas],
      'evaluation_focus': {
        'what_to_evaluate': issue.get('details', {}).get(
          'recommended_action', 'Evaluate the quality issue'
        ),
        'specific_problems': problem_snippets[:3],
        'key_questions': self._generate_quality_questions(issue_type, issue),
      },
      'trace_selection': {
        'method': 'Traces with confirmed quality issues',
        'evidence': problem_snippets[:2],
      },
    }

  def _create_mixed_quality_session(
    self,
    issues: List[Dict[str, Any]],
    schema_recommendations: List[Dict[str, Any]],
  ) -> Optional[Dict[str, Any]]:
    """Create a mixed session with traces showing different quality issues."""
    # Collect traces from different issue types for comparison
    mixed_traces = []
    mixed_problems = []

    for issue in issues[:5]:  # Take up to 5 different issue types
      example_traces = issue.get('example_traces', [])
      problem_snippets = issue.get('problem_snippets', [])
      issue_type = issue.get('issue_type', 'unknown')

      # Add 2-3 traces from each issue type
      for i, trace_id in enumerate(example_traces[:3]):
        mixed_traces.append(
          {
            'trace_id': trace_id,
            'issue_type': issue_type,
            'problem_example': problem_snippets[i]
            if i < len(problem_snippets)
            else f'{issue_type} issue',
          }
        )

    if len(mixed_traces) < 5:
      return None

    # Use comprehensive quality schemas
    comprehensive_schemas = [
      s
      for s in schema_recommendations
      if s.get('key')
      in ['correctness', 'response_quality', 'response_faithfulness', 'tone_professionalism']
    ]

    return {
      'session_name': 'Mixed Quality Issues Evaluation',
      'issue_type': 'mixed_quality',
      'issue_description': 'Diverse quality issues for comprehensive evaluation',
      'traces_with_issue': mixed_traces[:15],  # Cap at 15 traces
      'trace_count': len(mixed_traces[:15]),
      'recommended_schemas': [schema['key'] for schema in comprehensive_schemas],
      'evaluation_focus': {
        'what_to_evaluate': 'Various quality aspects across different issue types',
        'specific_problems': list(set([t['problem_example'] for t in mixed_traces[:5]])),
        'key_questions': [
          'Which quality issues are most severe?',
          'Are there common patterns across different problems?',
          'What are the priority areas for improvement?',
        ],
      },
      'trace_selection': {
        'method': 'Mixed sampling from different quality issues',
        'evidence': [f'{issue["title"]}' for issue in issues[:3]],
      },
    }

  def _create_edge_case_session(
    self,
    traces: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
    schema_recommendations: List[Dict[str, Any]],
  ) -> Optional[Dict[str, Any]]:
    """Create a session focused on edge cases and anomalies."""
    # Find statistical outliers and unusual patterns
    edge_cases = self._identify_edge_cases(traces)

    if len(edge_cases) < 5:  # Need sufficient edge cases
      return None

    # Limit to manageable number
    selected_edge_cases = edge_cases[:15]

    # Find schemas appropriate for anomaly assessment
    anomaly_schemas = [
      schema
      for schema in schema_recommendations
      if 'anomaly' in schema.get('key', '').lower() or 'efficiency' in schema.get('key', '').lower()
    ]

    # Add general quality schemas if no specific ones
    if not anomaly_schemas:
      anomaly_schemas = [
        schema
        for schema in schema_recommendations
        if schema.get('target_issue_type') in ['baseline_quality', 'general_quality']
      ][:2]

    return {
      'session_name': 'Edge Cases and Anomalies',
      'issue_type': 'edge_cases',
      'issue_description': 'Statistical outliers and unusual execution patterns',
      'anomalous_traces': [
        {
          'trace_id': case.get('trace_id'),
          'anomaly_type': case.get('anomaly_type'),
          'anomaly_description': case.get('description'),
        }
        for case in selected_edge_cases
      ],
      'trace_count': len(selected_edge_cases),
      'recommended_schemas': [schema['key'] for schema in anomaly_schemas],
      'evaluation_focus': {
        'what_to_evaluate': 'Whether unusual patterns indicate quality issues',
        'key_questions': [
          'Are these anomalies actually problems?',
          'What causes these unusual patterns?',
          'Is the agent behavior appropriate for these edge cases?',
        ],
      },
      'trace_selection': {
        'method': 'Statistical anomaly detection',
        'criteria': ['outliers', 'unusual_patterns'],
      },
    }

  def _find_traces_for_issue(
    self, traces: List[Dict[str, Any]], issue: Dict[str, Any]
  ) -> List[Dict[str, Any]]:
    """Find traces relevant to a specific issue."""
    issue_type = issue.get('issue_type', '')
    relevant_traces = []

    if issue_type == 'tool_failure_rate':
      # Find traces using the failing tools
      failing_tools = set()
      for tool_info in issue.get('details', {}).get('failing_tools', []):
        failing_tools.add(tool_info.get('tool', ''))

      for trace in traces:
        spans = trace.get('data', {}).get('spans', [])
        trace_tools = [span.get('name', '') for span in spans if span.get('span_type') == 'TOOL']

        if any(tool in failing_tools for tool in trace_tools):
          relevant_traces.append(trace)

    elif issue_type == 'latency_outliers':
      # Find traces with extreme latencies
      execution_times = [t.get('info', {}).get('execution_time_ms', 0) for t in traces]
      if execution_times:
        sorted_times = sorted(execution_times)
        p95_time = sorted_times[int(0.95 * len(sorted_times))] if len(sorted_times) > 0 else 0
        p5_time = sorted_times[int(0.05 * len(sorted_times))] if len(sorted_times) > 0 else 0

        for trace in traces:
          exec_time = trace.get('info', {}).get('execution_time_ms', 0)
          if exec_time >= p95_time or exec_time <= p5_time:
            relevant_traces.append(trace)

    elif issue_type == 'excessive_workflow_complexity':
      # Find traces with high span counts
      span_counts = [len(trace.get('data', {}).get('spans', [])) for trace in traces]
      if span_counts:
        avg_spans = sum(span_counts) / len(span_counts)
        threshold = avg_spans * 2

        for trace in traces:
          span_count = len(trace.get('data', {}).get('spans', []))
          if span_count > threshold:
            relevant_traces.append(trace)

    elif issue_type == 'unusual_tool_sequences':
      # Find traces with rare tool sequences (this is complex, simplified here)
      for trace in traces:
        spans = trace.get('data', {}).get('spans', [])
        tool_sequence = [span.get('name', '') for span in spans if span.get('span_type') == 'TOOL']

        # Simplified heuristic: traces with very long tool sequences or unusual patterns
        if len(tool_sequence) > 10 or len(set(tool_sequence)) < len(tool_sequence) / 3:
          relevant_traces.append(trace)

    else:
      # Default: use all traces (will be sampled later)
      relevant_traces = traces

    return relevant_traces

  def _select_representative_traces(
    self, traces: List[Dict[str, Any]], target_count: int, issue: Dict[str, Any]
  ) -> List[Dict[str, Any]]:
    """Select representative traces from the relevant set."""
    if len(traces) <= target_count:
      return traces

    # Sort traces by different criteria to get diversity
    diverse_selection = []

    # Sort by execution time and select across spectrum
    sorted_by_time = sorted(traces, key=lambda x: x.get('info', {}).get('execution_time_ms', 0))
    time_step = max(1, len(sorted_by_time) // (target_count // 2))
    diverse_selection.extend(sorted_by_time[::time_step][: target_count // 2])

    # Sort by span count and select remaining
    remaining_traces = [t for t in traces if t not in diverse_selection]
    sorted_by_spans = sorted(
      remaining_traces, key=lambda x: len(x.get('data', {}).get('spans', []))
    )
    span_step = max(1, len(sorted_by_spans) // (target_count - len(diverse_selection)))
    diverse_selection.extend(sorted_by_spans[::span_step][: target_count - len(diverse_selection)])

    # Return formatted trace info
    return [
      {
        'trace_id': trace.get('info', {}).get('trace_id'),
        'execution_time_ms': trace.get('info', {}).get('execution_time_ms', 0),
        'span_count': len(trace.get('data', {}).get('spans', [])),
        'selection_reason': self._get_selection_reason(trace, issue),
      }
      for trace in diverse_selection
    ]

  def _identify_edge_cases(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify edge cases and anomalies in the trace set."""
    edge_cases = []

    # Statistical analysis for outliers
    execution_times = [t.get('info', {}).get('execution_time_ms', 0) for t in traces]
    span_counts = [len(t.get('data', {}).get('spans', [])) for t in traces]

    if execution_times and span_counts:
      # Calculate statistics
      import statistics

      mean_time = statistics.mean(execution_times)
      std_time = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
      mean_spans = statistics.mean(span_counts)
      std_spans = statistics.stdev(span_counts) if len(span_counts) > 1 else 0

      for i, trace in enumerate(traces):
        exec_time = execution_times[i]
        span_count = span_counts[i]

        anomaly_score = 0
        anomaly_types = []

        # Time-based anomalies
        if std_time > 0:
          time_z_score = abs(exec_time - mean_time) / std_time
          if time_z_score > 2.5:  # > 2.5 sigma
            anomaly_score += time_z_score
            anomaly_types.append('execution_time_outlier')

        # Span count anomalies
        if std_spans > 0:
          span_z_score = abs(span_count - mean_spans) / std_spans
          if span_z_score > 2.5:  # > 2.5 sigma
            anomaly_score += span_z_score
            anomaly_types.append('complexity_outlier')

        # Tool usage anomalies
        spans = trace.get('data', {}).get('spans', [])
        tool_spans = [s for s in spans if s.get('span_type') == 'TOOL']
        if tool_spans:
          tool_names = [s.get('name', '') for s in tool_spans]
          unique_tools = len(set(tool_names))
          total_tools = len(tool_names)

          # High repetition anomaly
          if total_tools > 5 and unique_tools / total_tools < 0.3:  # < 30% unique
            anomaly_score += 2
            anomaly_types.append('tool_repetition_anomaly')

        if anomaly_score > 2 and anomaly_types:  # Threshold for inclusion
          edge_cases.append(
            {
              'trace_id': trace.get('info', {}).get('trace_id'),
              'anomaly_score': round(anomaly_score, 2),
              'anomaly_type': ', '.join(anomaly_types),
              'description': self._describe_anomaly(trace, anomaly_types, exec_time, span_count),
            }
          )

    # Sort by anomaly score
    edge_cases.sort(key=lambda x: x['anomaly_score'], reverse=True)

    return edge_cases

  def _describe_anomaly(
    self, trace: Dict[str, Any], anomaly_types: List[str], exec_time: int, span_count: int
  ) -> str:
    """Generate a description of the anomaly."""
    descriptions = []

    if 'execution_time_outlier' in anomaly_types:
      if exec_time > 30000:  # > 30 seconds
        descriptions.append(f'Extremely slow execution ({exec_time / 1000:.1f}s)')
      elif exec_time < 1000:  # < 1 second
        descriptions.append(f'Extremely fast execution ({exec_time}ms)')
      else:
        descriptions.append(f'Unusual execution time ({exec_time / 1000:.1f}s)')

    if 'complexity_outlier' in anomaly_types:
      descriptions.append(f'Unusual workflow complexity ({span_count} spans)')

    if 'tool_repetition_anomaly' in anomaly_types:
      descriptions.append('High tool repetition pattern')

    return '; '.join(descriptions) if descriptions else 'Statistical anomaly detected'

  def _classify_performance_tier(
    self, trace: Dict[str, Any], all_execution_times: List[int]
  ) -> str:
    """Classify a trace into performance tier."""
    exec_time = trace.get('info', {}).get('execution_time_ms', 0)
    sorted_times = sorted(all_execution_times)
    n = len(sorted_times)

    p33 = sorted_times[int(0.33 * n)] if n > 0 else 0
    p67 = sorted_times[int(0.67 * n)] if n > 0 else 0

    if exec_time <= p33:
      return 'fast'
    elif exec_time <= p67:
      return 'medium'
    else:
      return 'slow'

  def _get_optimal_session_size(self, issue_type: str, severity: str) -> int:
    """Get optimal session size based on issue type and severity."""
    base_sizes = {'critical': 25, 'high': 20, 'medium': 15, 'low': 10}

    return base_sizes.get(severity, 15)

  def _calculate_session_priority(self, issue: Dict[str, Any], trace_count: int) -> str:
    """Calculate session priority based on issue severity and trace count."""
    severity = issue.get('severity', 'medium')
    severity_score = issue.get('severity_score', 0)

    if severity == 'critical' or severity_score > 50:
      return 'critical'
    elif severity == 'high' or severity_score > 25:
      return 'high'
    elif trace_count > 15:
      return 'medium'
    else:
      return 'low'

  def _calculate_impact_score(self, issue: Dict[str, Any], trace_count: int) -> int:
    """Calculate potential impact score for the session."""
    severity_scores = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25}
    base_score = severity_scores.get(issue.get('severity', 'medium'), 50)

    # Adjust based on trace count and affected traces
    affected_traces = issue.get('affected_traces', 0)
    trace_factor = min(1.5, trace_count / 10.0)  # Up to 1.5x multiplier
    affected_factor = min(1.3, affected_traces / 20.0)  # Up to 1.3x multiplier

    return int(base_score * trace_factor * affected_factor)

  def _estimate_completion_time(self, trace_count: int, schema_count: int) -> str:
    """Estimate time to complete the labeling session."""
    # Rough estimate: 3-5 minutes per trace per schema
    minutes_per_item = 4 * schema_count
    total_minutes = trace_count * minutes_per_item

    if total_minutes < 60:
      return f'{total_minutes}m'
    else:
      hours = total_minutes // 60
      remaining_minutes = total_minutes % 60
      return f'{hours}h {remaining_minutes}m'

  def _generate_quality_questions(self, issue_type: str, issue: Dict[str, Any]) -> List[str]:
    """Generate quality-focused evaluation questions."""
    questions_map = {
      'response_faithfulness': [
        'Does the response accurately reflect tool outputs?',
        'Are there any fabricated or hallucinated details?',
        'Is the agent being honest about tool results?',
      ],
      'tool_failure_rate': [
        'Was the right tool selected for this task?',
        'What tool should have been used instead?',
        'Why did the selected tool fail?',
      ],
      'tone_professionalism': [
        'Is the tone appropriate and professional?',
        'Are there any unprofessional phrases or weird language?',
        'How could the response be more polished?',
      ],
      'logical_consistency': [
        'Are there contradictions in the response?',
        'Is the logic sound and coherent?',
        'Are facts presented accurately?',
      ],
      'response_completeness': [
        'Is all necessary information provided?',
        'Are there important details missing?',
        "Does the response fully address the user's needs?",
      ],
      'redundant_tool_usage': [
        'Could fewer tool calls achieve the same result?',
        'Why was the same tool called multiple times?',
        'What would be a more efficient approach?',
      ],
    }

    return questions_map.get(
      issue_type,
      [
        'What quality issues do you see?',
        'How could this response be improved?',
        'Is the information accurate and complete?',
      ],
    )

  def _get_selection_criteria(self, issue: Dict[str, Any]) -> List[str]:
    """Get the criteria used for trace selection."""
    issue_type = issue.get('issue_type', '')

    criteria_map = {
      'tool_failure_rate': ['tool_usage_patterns', 'failure_indicators'],
      'latency_outliers': ['execution_time_percentiles', 'performance_extremes'],
      'excessive_workflow_complexity': ['span_count_thresholds', 'complexity_metrics'],
      'unusual_tool_sequences': ['sequence_rarity', 'workflow_patterns'],
    }

    return criteria_map.get(issue_type, ['general_diversity', 'representative_sampling'])

  def _get_selection_reason(self, trace: Dict[str, Any], issue: Dict[str, Any]) -> str:
    """Get reason why this trace was selected."""
    issue_type = issue.get('issue_type', '')
    exec_time = trace.get('info', {}).get('execution_time_ms', 0)
    span_count = len(trace.get('data', {}).get('spans', []))

    if issue_type == 'tool_failure_rate':
      return 'Contains tools with high failure rates'
    elif issue_type == 'latency_outliers':
      return f'Execution time outlier ({exec_time}ms)'
    elif issue_type == 'excessive_workflow_complexity':
      return f'High workflow complexity ({span_count} spans)'
    else:
      return 'Representative of issue pattern'

  def _create_baseline_quality_session(
    self, traces: List[Dict[str, Any]], schema_recommendations: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """Create baseline quality evaluation session."""
    if not traces:
      return []

    # Sample traces for quality baseline
    session_size = min(20, len(traces))

    if len(traces) > session_size:
      step = len(traces) // session_size
      sampled_traces = traces[::step][:session_size]
    else:
      sampled_traces = traces

    # Use quality-focused schemas
    quality_schemas = [
      schema
      for schema in schema_recommendations
      if any(
        term in schema.get('key', '').lower()
        for term in ['quality', 'correctness', 'faithfulness', 'tone']
      )
    ]

    return [
      {
        'session_name': 'Baseline Quality Evaluation',
        'issue_type': 'baseline_quality',
        'issue_description': 'General quality assessment to establish baseline',
        'traces_with_issue': [
          {
            'trace_id': trace.get('info', {}).get('trace_id'),
            'problem_example': 'Baseline quality assessment needed',
          }
          for trace in sampled_traces
        ],
        'trace_count': len(sampled_traces),
        'recommended_schemas': [schema['key'] for schema in quality_schemas],
        'evaluation_focus': {
          'what_to_evaluate': 'Overall response quality, accuracy, and professionalism',
          'specific_problems': ['General quality baseline needed'],
          'key_questions': [
            'Is the information accurate and complete?',
            'Is the tone professional and appropriate?',
            'Are there any quality issues?',
          ],
        },
        'trace_selection': {
          'method': 'Representative sample for baseline',
          'evidence': ['Random sampling across all traces'],
        },
      }
    ]
