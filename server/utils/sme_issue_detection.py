"""SME Issue Detection Utility

This module identifies quality issues in AI agent responses that require evaluation.
It focuses on correctness, faithfulness, professionalism, and other quality aspects.
All issues are grounded in specific trace examples.
"""

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SMEIssueDetector:
  """Detects quality issues in agent traces with concrete examples."""

  def __init__(self):
    self.logger = logging.getLogger(__name__)

  def detect_critical_issues(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect quality issues in traces with specific examples.

    Args:
        traces: List of trace dictionaries with info, data, and spans

    Returns:
        Dictionary with quality issues, each grounded in trace examples
    """
    if not traces:
      return {'issues': [], 'summary': {'total_traces': 0, 'issues_detected': 0}}

    self.logger.info(f'Analyzing {len(traces)} traces for quality issues')

    issues = []

    # 1. Response Faithfulness Issues - Check if responses match tool outputs
    faithfulness_issues = self._detect_faithfulness_issues(traces)
    if faithfulness_issues:
      issues.extend(faithfulness_issues)

    # 2. Tool Selection Quality - Wrong tools being used
    tool_quality_issues = self._detect_tool_quality_issues(traces)
    if tool_quality_issues:
      issues.extend(tool_quality_issues)

    # 3. Response Quality Problems - Weird phrasing, tone issues
    response_quality_issues = self._detect_response_quality_issues(traces)
    if response_quality_issues:
      issues.extend(response_quality_issues)

    # 4. Correctness Issues - Factual errors, logic problems
    correctness_issues = self._detect_correctness_issues(traces)
    if correctness_issues:
      issues.extend(correctness_issues)

    # 5. Completeness Issues - Missing information
    completeness_issues = self._detect_completeness_issues(traces)
    if completeness_issues:
      issues.extend(completeness_issues)

    # Sort by severity and number of examples
    issues.sort(
      key=lambda x: (
        {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}[x.get('severity', 'medium')],
        len(x.get('example_traces', [])),
      ),
      reverse=True,
    )

    return {
      'issues': issues,
      'summary': {
        'total_traces': len(traces),
        'issues_detected': len(issues),
        'critical_issues': len([i for i in issues if i.get('severity') == 'critical']),
        'high_issues': len([i for i in issues if i.get('severity') == 'high']),
        'medium_issues': len([i for i in issues if i.get('severity') == 'medium']),
      },
      'raw_data': {'traces_analyzed': len(traces)},
    }

  def _detect_faithfulness_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect when responses don't match tool outputs."""
    issues = []
    unfaithful_traces = []
    problem_snippets = []

    for trace in traces[:50]:  # Sample first 50 for analysis
      trace_id = trace.get('info', {}).get('trace_id', 'unknown')
      spans = trace.get('data', {}).get('spans', [])

      # Look for tool outputs and final responses
      tool_outputs = []
      final_responses = []

      for span in spans:
        span_type = span.get('span_type', '')
        if span_type == 'TOOL':
          outputs = span.get('outputs', {})
          if outputs:
            tool_outputs.append(str(outputs))

        elif span_type in ['LLM', 'CHAT_MODEL']:
          outputs = span.get('outputs', {})
          if outputs:
            final_responses.append(str(outputs))

      # Check for potential faithfulness issues
      if tool_outputs and final_responses:
        # Simple heuristic: if tool output has numbers/data that doesn't appear in response
        for tool_out in tool_outputs:
          # Look for data patterns (numbers, specific terms) not in response
          if any(term in tool_out.lower() for term in ['error', 'failed', 'exception']):
            # Tool had error, but check if response acknowledges it
            response_text = ' '.join(final_responses).lower()
            if not any(
              err_term in response_text
              for err_term in ['error', 'failed', 'could not', 'unable', 'problem']
            ):
              unfaithful_traces.append(trace_id)
              problem_snippets.append(f'Tool error "{tool_out[:100]}" not reflected in response')
              break

    if unfaithful_traces:
      issues.append(
        {
          'issue_type': 'response_faithfulness',
          'severity': 'high',
          'severity_score': 80,
          'title': 'Responses Not Faithful to Tool Outputs',
          'description': 'Agent responses do not accurately reflect tool outputs, potentially fabricating information',
          'affected_traces': len(unfaithful_traces),
          'example_traces': unfaithful_traces[:5],
          'problem_snippets': problem_snippets[:3],
          'details': {
            'pattern': 'Tool errors or outputs not properly reflected in responses',
            'recommended_action': 'Evaluate whether responses accurately convey tool results',
          },
        }
      )

    return issues

  def _detect_tool_quality_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect wrong or inappropriate tool usage."""
    issues = []
    tool_problems = defaultdict(list)  # tool -> [trace_ids]
    problem_snippets = []

    for trace in traces[:50]:
      trace_id = trace.get('info', {}).get('trace_id', 'unknown')
      spans = trace.get('data', {}).get('spans', [])

      # Analyze tool usage patterns
      tools_used = []
      for span in spans:
        if span.get('span_type') == 'TOOL':
          tool_name = span.get('name', 'unknown')
          tools_used.append(tool_name)

          # Check for tool failures or errors
          outputs = span.get('outputs', {})
          if any(
            err in str(outputs).lower()
            for err in ['error', 'exception', 'failed', 'not found', 'invalid']
          ):
            tool_problems[tool_name].append(trace_id)
            problem_snippets.append(f'{tool_name} failed: {str(outputs)[:100]}')

      # Check for redundant tool usage
      tool_counts = Counter(tools_used)
      for tool, count in tool_counts.items():
        if count > 3:  # Same tool used more than 3 times
          tool_problems['redundant_usage'].append(trace_id)
          problem_snippets.append(f'{tool} called {count} times - potential inefficiency')

    # Create issues for problematic tools
    if tool_problems:
      failing_tools = [t for t in tool_problems if t != 'redundant_usage']
      if failing_tools:
        issues.append(
          {
            'issue_type': 'tool_failure_rate',
            'severity': 'high' if len(failing_tools) > 3 else 'medium',
            'severity_score': 70,
            'title': 'High Tool Failure Rate',
            'description': f'Tools failing frequently: {", ".join(failing_tools[:3])}',
            'affected_traces': sum(len(traces) for traces in tool_problems.values()),
            'example_traces': list(set(sum(tool_problems.values(), [])))[:5],
            'problem_snippets': problem_snippets[:3],
            'details': {
              'failing_tools': [
                {'tool': tool, 'failure_count': len(tool_problems[tool])}
                for tool in failing_tools[:5]
              ],
              'recommended_action': 'Evaluate if correct tools are being selected for tasks',
            },
          }
        )

      if 'redundant_usage' in tool_problems:
        issues.append(
          {
            'issue_type': 'redundant_tool_usage',
            'severity': 'medium',
            'severity_score': 50,
            'title': 'Redundant Tool Usage',
            'description': 'Same tools being called multiple times unnecessarily',
            'affected_traces': len(tool_problems['redundant_usage']),
            'example_traces': tool_problems['redundant_usage'][:5],
            'problem_snippets': [s for s in problem_snippets if 'times' in s][:3],
            'details': {
              'recommended_action': 'Evaluate workflow efficiency and tool usage patterns'
            },
          }
        )

    return issues

  def _detect_response_quality_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect tone, style, and professionalism issues."""
    issues = []
    quality_problems = []
    problem_snippets = []

    # Keywords indicating potential quality issues
    unprofessional_patterns = [
      'wtf',
      'lol',
      'omg',
      'damn',
      'crap',
      'sucks',
      'stupid',
      'dumb',
      'weird',
      'ugh',
      'meh',
      'whatever',
    ]

    weird_patterns = [
      'beep boop',
      'oopsie',
      'whoopsie',
      'thingy',
      'stuff and things',
      'blah blah',
      'yada yada',
      '...',
      '!!!',
      '???',
    ]

    for trace in traces[:50]:
      trace_id = trace.get('info', {}).get('trace_id', 'unknown')
      spans = trace.get('data', {}).get('spans', [])

      for span in spans:
        if span.get('span_type') in ['LLM', 'CHAT_MODEL']:
          outputs = str(span.get('outputs', {})).lower()

          # Check for unprofessional language
          for pattern in unprofessional_patterns:
            if pattern in outputs:
              quality_problems.append(trace_id)
              snippet = self._extract_snippet_around_pattern(outputs, pattern, 50)
              problem_snippets.append(f'Unprofessional: "{snippet}"')
              break

          # Check for weird phrasing
          for pattern in weird_patterns:
            if pattern in outputs:
              quality_problems.append(trace_id)
              snippet = self._extract_snippet_around_pattern(outputs, pattern, 50)
              problem_snippets.append(f'Weird phrasing: "{snippet}"')
              break

          # Check for excessive exclamation or question marks
          if outputs.count('!') > 3 or outputs.count('?') > 3:
            quality_problems.append(trace_id)
            problem_snippets.append('Excessive punctuation detected')

    if quality_problems:
      issues.append(
        {
          'issue_type': 'tone_professionalism',
          'severity': 'medium',
          'severity_score': 60,
          'title': 'Tone and Professionalism Issues',
          'description': 'Responses contain unprofessional language or weird phrasing',
          'affected_traces': len(set(quality_problems)),
          'example_traces': list(set(quality_problems))[:5],
          'problem_snippets': problem_snippets[:5],
          'details': {
            'patterns_found': 'Unprofessional language, weird phrasing, excessive punctuation',
            'recommended_action': 'Evaluate tone, style, and professionalism of responses',
          },
        }
      )

    return issues

  def _detect_correctness_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect potential factual errors and logic problems."""
    issues = []
    correctness_problems = []
    problem_snippets = []

    # Patterns suggesting potential correctness issues
    contradiction_patterns = [
      ('yes', 'no'),
      ('true', 'false'),
      ('correct', 'incorrect'),
      ('will', "won't"),
      ('can', "can't"),
      ('is', "isn't"),
    ]

    uncertainty_patterns = [
      'i think',
      'maybe',
      'possibly',
      'probably',
      'might be',
      'could be',
      'not sure',
      'unclear',
      "don't know",
      'unsure',
    ]

    for trace in traces[:50]:
      trace_id = trace.get('info', {}).get('trace_id', 'unknown')
      spans = trace.get('data', {}).get('spans', [])

      response_texts = []
      for span in spans:
        if span.get('span_type') in ['LLM', 'CHAT_MODEL']:
          outputs = str(span.get('outputs', {})).lower()
          response_texts.append(outputs)

      # Check for contradictions within the same trace
      full_response = ' '.join(response_texts)
      for pos_term, neg_term in contradiction_patterns:
        if pos_term in full_response and neg_term in full_response:
          # Found potential contradiction
          correctness_problems.append(trace_id)
          problem_snippets.append(
            f'Potential contradiction: uses both "{pos_term}" and "{neg_term}"'
          )
          break

      # Check for excessive uncertainty
      uncertainty_count = sum(1 for pattern in uncertainty_patterns if pattern in full_response)
      if uncertainty_count > 2:
        correctness_problems.append(trace_id)
        problem_snippets.append(f'Excessive uncertainty: {uncertainty_count} uncertain phrases')

    if correctness_problems:
      issues.append(
        {
          'issue_type': 'logical_consistency',
          'severity': 'high',
          'severity_score': 75,
          'title': 'Logical Consistency and Correctness Concerns',
          'description': 'Responses contain contradictions or excessive uncertainty',
          'affected_traces': len(set(correctness_problems)),
          'example_traces': list(set(correctness_problems))[:5],
          'problem_snippets': problem_snippets[:5],
          'details': {
            'patterns_found': 'Contradictions, excessive uncertainty, logic issues',
            'recommended_action': 'Evaluate factual accuracy and logical consistency',
          },
        }
      )

    return issues

  def _detect_completeness_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect incomplete or truncated responses."""
    issues = []
    incomplete_traces = []
    problem_snippets = []

    # Patterns suggesting incomplete responses
    incomplete_patterns = [
      'TODO',
      'FIXME',
      'TBD',
      '...',
      'etc.',
      'and so on',
      'and more',
      'to be continued',
      'more to come',
    ]

    truncation_patterns = ['...', '…', '[truncated]', '[cut off]', '[continued]']

    for trace in traces[:50]:
      trace_id = trace.get('info', {}).get('trace_id', 'unknown')
      spans = trace.get('data', {}).get('spans', [])

      for span in spans:
        if span.get('span_type') in ['LLM', 'CHAT_MODEL']:
          outputs = str(span.get('outputs', {}))

          # Check for incomplete patterns
          for pattern in incomplete_patterns:
            if pattern in outputs:
              incomplete_traces.append(trace_id)
              snippet = self._extract_snippet_around_pattern(outputs, pattern, 50)
              problem_snippets.append(f'Incomplete: "{snippet}"')
              break

          # Check if response seems truncated (ends abruptly)
          if outputs.rstrip().endswith(tuple(truncation_patterns)):
            incomplete_traces.append(trace_id)
            problem_snippets.append(f'Truncated response: "...{outputs[-50:]}"')

    if incomplete_traces:
      issues.append(
        {
          'issue_type': 'response_completeness',
          'severity': 'medium',
          'severity_score': 55,
          'title': 'Incomplete or Truncated Responses',
          'description': 'Responses appear incomplete or cut off',
          'affected_traces': len(set(incomplete_traces)),
          'example_traces': list(set(incomplete_traces))[:5],
          'problem_snippets': problem_snippets[:5],
          'details': {
            'patterns_found': 'TODO markers, truncation, incomplete thoughts',
            'recommended_action': 'Evaluate response completeness and whether all user needs are addressed',
          },
        }
      )

    return issues

  def _extract_snippet_around_pattern(
    self, text: str, pattern: str, context_length: int = 50
  ) -> str:
    """Extract a snippet of text around a pattern for context."""
    pattern_idx = text.find(pattern)
    if pattern_idx == -1:
      return pattern

    start = max(0, pattern_idx - context_length)
    end = min(len(text), pattern_idx + len(pattern) + context_length)

    snippet = text[start:end]
    if start > 0:
      snippet = '...' + snippet
    if end < len(text):
      snippet = snippet + '...'

    return snippet.replace('\n', ' ').strip()
