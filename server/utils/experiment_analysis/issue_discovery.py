"""Open-ended Issue Discovery Module

Uses LLM to discover quality issues in traces without predefined categories.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class IssueDiscovery:
  """Discovers quality issues in traces using open-ended LLM analysis."""

  def __init__(self, model_client):
    """Initialize with model serving client."""
    self.model_client = model_client
    self.logger = logging.getLogger(__name__)

  async def discover_issues(
    self, traces: List[Dict[str, Any]], experiment_info: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Discover quality issues using chain-of-thought LLM analysis.

    Args:
        traces: List of trace data to analyze
        experiment_info: Experiment metadata for context

    Returns:
        Dictionary with discovered issues and full trace mappings
    """
    self.logger.info(f'Starting open-ended issue discovery for {len(traces)} traces')

    # Step 1: Understand what the agent does
    agent_understanding = self._understand_agent_purpose(traces, experiment_info)

    # Step 2: Proactively detect performance issues
    performance_issues = self._detect_performance_issues(traces)

    # Step 3: Discover additional issue categories via LLM
    discovered_categories = self._discover_issue_categories(traces, agent_understanding)

    # Step 4: Systematic analysis with ALL trace IDs
    comprehensive_issues = self._analyze_all_traces(
      traces, discovered_categories, agent_understanding
    )

    # Step 5: Combine performance issues with LLM-discovered issues
    all_issues = performance_issues + comprehensive_issues

    # Step 6: Aggregate and organize
    organized_issues = self._organize_issues(all_issues)

    return {
      'agent_understanding': agent_understanding,
      'discovered_categories': discovered_categories,
      'issues': organized_issues,
      'metadata': {
        'total_traces_analyzed': len(traces),
        'unique_issue_types': len(organized_issues),
        'discovery_method': 'open-ended-llm',
      },
    }

  def _understand_agent_purpose(
    self, traces: List[Dict[str, Any]], experiment_info: Dict[str, Any]
  ) -> str:
    """First understand what this agent is supposed to do."""
    # Sample a few traces for understanding
    sample_traces = traces[:5] if len(traces) > 5 else traces

    # Extract requests and responses from traces
    interactions = []
    for trace in sample_traces:
      # Try to get request/response from trace data first
      request_text = trace.get('data', {}).get('request', None)
      response_text = trace.get('data', {}).get('response', None)

      # If not found, extract from spans
      if not request_text or not response_text:
        for span in trace.get('data', {}).get('spans', []):
          # Get user query from agent input
          if not request_text and span.get('inputs'):
            if 'messages' in span.get('inputs', {}):
              msgs = span['inputs']['messages']
              if msgs and isinstance(msgs, list) and len(msgs) > 0:
                last_msg = msgs[-1]
                if isinstance(last_msg, dict) and 'content' in last_msg:
                  request_text = last_msg['content']
            elif 'input' in span.get('inputs', {}):
              request_text = span['inputs']['input']

          # Get response from agent output
          if not response_text and span.get('outputs'):
            if 'generations' in span.get('outputs', {}):
              gens = span['outputs']['generations']
              if gens and isinstance(gens, list) and len(gens) > 0:
                if isinstance(gens[0], list) and len(gens[0]) > 0:
                  gen = gens[0][0]
                  if 'text' in gen:
                    response_text = gen['text']
            elif 'output' in span.get('outputs', {}):
              response_text = span['outputs']['output']

      interaction = {
        'request': request_text or 'No request found',
        'response': response_text or 'No response found',
        'tools_used': self._extract_tool_names(trace),
        'execution_time_ms': trace.get('info', {}).get('execution_time_ms', 0),
        'status': trace.get('info', {}).get('status', 'unknown'),
      }
      interactions.append(interaction)

    prompt = f"""
        ## Chain of Thought: Understanding the Agent
        
        Experiment: {experiment_info.get('name', 'Unknown')}
        
        Sample interactions:
        {json.dumps(interactions, indent=2)}
        
        Based on these interactions, describe in 2-3 sentences:
        1. What type of agent is this? (e.g., Databricks assistant, SQL helper, code generator, etc.)
        2. What are its primary capabilities and tools?
        3. What is the typical use case?
        
        Be specific and concise. If this appears to be a Databricks-related assistant, mention that explicitly.
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint,
      messages=[{'role': 'user', 'content': prompt}],
    )

    # Extract content from the correct response structure
    if response and 'choices' in response and response['choices']:
      choice = response['choices'][0]
      if 'message' in choice and 'content' in choice['message']:
        return choice['message']['content']

    return 'Unknown agent type'

  def _discover_issue_categories(
    self, traces: List[Dict[str, Any]], agent_understanding: str
  ) -> List[Dict[str, Any]]:
    """Discover what types of issues exist in this specific data."""
    # Sample more traces for discovery
    sample_traces = traces[:20] if len(traces) > 20 else traces

    # Prepare trace summaries with better extraction
    trace_summaries = []
    for trace in sample_traces:
      # Extract request/response properly
      request_text = self._extract_request(trace)
      response_text = self._extract_response(trace)

      summary = {
        'trace_id': trace.get('info', {}).get('trace_id'),
        'status': trace.get('info', {}).get('status'),
        'execution_time_ms': trace.get('info', {}).get('execution_time_ms', 0),
        'request_preview': request_text[:200] if request_text else 'No request found',
        'response_preview': response_text[:200] if response_text else 'No response found',
        'tool_errors': self._extract_tool_errors(trace),
        'spans_count': len(trace.get('data', {}).get('spans', [])),
        'tools_used': self._extract_tool_names(trace),
      }
      trace_summaries.append(summary)

    prompt = f"""
        ## Chain of Thought: Issue Discovery
        
        Agent Understanding:
        {agent_understanding}
        
        Trace Data:
        {json.dumps(trace_summaries, indent=2)}
        
        Analyze these traces carefully to discover ANY quality issues, including:
        - Performance issues (slow responses, timeouts)
        - Error handling problems
        - Incomplete or unhelpful responses
        - Tool usage issues
        - Any other problems you observe
        
        BE SENSITIVE - even minor issues should be reported.
        
        For each issue type you discover:
        1. Give it a descriptive name
        2. Explain what's wrong
        3. Explain why it matters
        4. List ALL trace IDs that exhibit this issue
        5. Provide example snippets
        
        Return JSON:
        {{
            "discovered_issue_types": [
                {{
                    "issue_name": "descriptive_name_for_issue",
                    "category": "broader_category",
                    "description": "what's wrong",
                    "why_it_matters": "impact on users/system",
                    "example_trace_ids": ["trace_id1", "trace_id2"],
                    "problem_snippets": ["example of the problem"],
                    "suggested_evaluation": "IMPORTANT: Phrase as a TRUE/FALSE statement like 'The response is correct' or 'The agent handled the error properly'"
                }}
            ]
        }}
        
        Be specific to this domain and these actual problems you observe.
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint,
      messages=[{'role': 'user', 'content': prompt}],
    )

    # Extract content from the correct response structure
    content = '{}'
    if response and 'choices' in response and response['choices']:
      choice = response['choices'][0]
      if 'message' in choice and 'content' in choice['message']:
        content = choice['message']['content']

    try:
      result = json.loads(content)
      return result.get('discovered_issue_types', [])
    except json.JSONDecodeError:
      self.logger.error(f'Failed to parse discovery response: {content[:500]}')
      return []

  def _analyze_all_traces(
    self,
    traces: List[Dict[str, Any]],
    discovered_categories: List[Dict[str, Any]],
    agent_understanding: str,
  ) -> List[Dict[str, Any]]:
    """Analyze ALL traces systematically for discovered issues."""
    # Prepare all trace IDs and summaries
    all_trace_data = []
    for trace in traces:
      trace_data = {
        'trace_id': trace.get('info', {}).get('trace_id'),
        'status': trace.get('info', {}).get('status'),
        'has_errors': self._has_errors(trace),
        'request_hash': str(hash(str(trace.get('data', {}).get('request', ''))))[:8],
        'response_hash': str(hash(str(trace.get('data', {}).get('response', ''))))[:8],
        'tool_count': len(self._extract_tool_names(trace)),
      }
      all_trace_data.append(trace_data)

    prompt = f"""
        ## Chain of Thought: Comprehensive Issue Analysis
        
        Agent Understanding:
        {agent_understanding}
        
        Discovered Issue Categories:
        {json.dumps(discovered_categories, indent=2)}
        
        ALL Trace Data ({len(traces)} traces):
        {json.dumps(all_trace_data, indent=2)}
        
        Now analyze ALL traces for the discovered issues.
        For each issue type:
        1. Count EXACTLY how many traces have this issue
        2. List ALL trace IDs that exhibit this issue (not just examples)
        3. Provide 2-3 example problem snippets
        4. Assign severity: critical/high/medium/low
        5. Determine if this needs FEEDBACK (human judgment) or EXPECTATION (ground truth)
        
        Also look for any NEW issues not in the discovered categories.
        
        Return JSON:
        {{
            "comprehensive_issues": [
                {{
                    "issue_type": "issue_name",
                    "severity": "high",
                    "description": "detailed description",
                    "total_affected_traces": <exact_count>,
                    "all_affected_trace_ids": ["EVERY trace ID with this issue"],
                    "example_snippets": ["2-3 examples max"],
                    "requires_feedback": true/false,
                    "requires_expectation": true/false,
                    "evaluation_question": "MUST be a TRUE/FALSE statement like: 'The response correctly addresses the user request' or 'The agent used appropriate tools for this task'"
                }}
            ]
        }}
        
        CRITICAL: Include EVERY trace ID affected, not just examples!
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint,
      messages=[{'role': 'user', 'content': prompt}],
    )

    # Extract content from the correct response structure
    content = '{}'
    if response and 'choices' in response and response['choices']:
      choice = response['choices'][0]
      if 'message' in choice and 'content' in choice['message']:
        content = choice['message']['content']

    try:
      result = json.loads(content)
      return result.get('comprehensive_issues', [])
    except json.JSONDecodeError:
      self.logger.error(f'Failed to parse comprehensive analysis: {content[:500]}')
      return []

  def _organize_issues(self, comprehensive_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Organize and validate discovered issues."""
    organized = []
    for issue in comprehensive_issues:
      # Ensure we have all trace IDs
      all_trace_ids = issue.get('all_affected_trace_ids', [])

      # Validate trace count matches
      stated_count = issue.get('total_affected_traces', 0)
      actual_count = len(all_trace_ids)

      if stated_count != actual_count:
        self.logger.warning(
          f'Issue {issue.get("issue_type")}: '
          f'stated {stated_count} traces but found {actual_count} IDs'
        )

      organized_issue = {
        'issue_type': issue.get('issue_type', 'unknown'),
        'severity': issue.get('severity', 'medium'),
        'title': issue.get('issue_type', '').replace('_', ' ').title(),
        'description': issue.get('description', ''),
        'affected_traces': actual_count,  # Use actual count
        'example_traces': all_trace_ids[:5],  # First 5 for UI display
        'all_trace_ids': all_trace_ids,  # ALL trace IDs
        'problem_snippets': issue.get('example_snippets', [])[:2],
        'requires_feedback': issue.get('requires_feedback', True),
        'requires_expectation': issue.get('requires_expectation', False),
        'evaluation_question': issue.get('evaluation_question', ''),
      }

      organized.append(organized_issue)

    # Sort by severity and affected traces
    organized.sort(
      key=lambda x: (
        {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x['severity']],
        x['affected_traces'],
      ),
      reverse=True,
    )

    return organized

  def _extract_request(self, trace: Dict[str, Any]) -> str:
    """Extract user request from trace."""
    # Try trace data first
    if trace.get('data', {}).get('request'):
      return str(trace['data']['request'])

    # Extract from spans
    for span in trace.get('data', {}).get('spans', []):
      if span.get('inputs'):
        # Check for messages (common in agent spans)
        if 'messages' in span.get('inputs', {}):
          msgs = span['inputs']['messages']
          if msgs and isinstance(msgs, list) and len(msgs) > 0:
            last_msg = msgs[-1]
            if isinstance(last_msg, dict) and 'content' in last_msg:
              return last_msg['content']
        # Check for direct input field
        elif 'input' in span.get('inputs', {}):
          return str(span['inputs']['input'])

    return ''

  def _extract_response(self, trace: Dict[str, Any]) -> str:
    """Extract agent response from trace."""
    # Try trace data first
    if trace.get('data', {}).get('response'):
      return str(trace['data']['response'])

    # Extract from spans
    for span in trace.get('data', {}).get('spans', []):
      if span.get('outputs'):
        # Check for generations (common in LLM spans)
        if 'generations' in span.get('outputs', {}):
          gens = span['outputs']['generations']
          if gens and isinstance(gens, list) and len(gens) > 0:
            if isinstance(gens[0], list) and len(gens[0]) > 0:
              gen = gens[0][0]
              if 'text' in gen:
                return gen['text']
        # Check for direct output field
        elif 'output' in span.get('outputs', {}):
          return str(span['outputs']['output'])
        # Check for choices (common in chat completions)
        elif 'choices' in span.get('outputs', {}):
          choices = span['outputs']['choices']
          if choices and isinstance(choices, list) and len(choices) > 0:
            choice = choices[0]
            if 'message' in choice and 'content' in choice['message']:
              return choice['message']['content']

    return ''

  def _detect_performance_issues(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Proactively detect performance issues based on thresholds."""
    issues = []

    # Check for slow responses
    slow_traces = []
    very_slow_traces = []

    for trace in traces:
      exec_time = trace.get('info', {}).get('execution_time_ms', 0)
      trace_id = trace.get('info', {}).get('trace_id')

      if exec_time > 30000:  # > 30 seconds
        very_slow_traces.append({'trace_id': trace_id, 'execution_time_ms': exec_time})
      elif exec_time > 10000:  # > 10 seconds
        slow_traces.append({'trace_id': trace_id, 'execution_time_ms': exec_time})

    # Create issues for performance problems
    if very_slow_traces:
      issues.append(
        {
          'issue_type': 'critical_response_latency',
          'severity': 'critical',
          'category': 'performance',
          'description': 'Responses taking over 30 seconds, severely impacting user experience',
          'why_it_matters': 'Users will likely abandon requests or experience timeouts',
          'total_affected_traces': len(very_slow_traces),
          'all_affected_trace_ids': [t['trace_id'] for t in very_slow_traces],
          'example_snippets': [
            f'Trace {t["trace_id"]}: {t["execution_time_ms"]}ms' for t in very_slow_traces[:3]
          ],
          'evaluation_question': 'The response was delivered within acceptable time limits (<10s)',
          'requires_feedback': False,  # Performance is objective, not subjective
          'requires_expectation': False,
        }
      )

    if slow_traces:
      issues.append(
        {
          'issue_type': 'high_response_latency',
          'severity': 'high',
          'category': 'performance',
          'description': 'Responses taking 10-30 seconds, degrading user experience',
          'why_it_matters': 'Users experience frustrating delays waiting for responses',
          'total_affected_traces': len(slow_traces),
          'all_affected_trace_ids': [t['trace_id'] for t in slow_traces],
          'example_snippets': [
            f'Trace {t["trace_id"]}: {t["execution_time_ms"]}ms' for t in slow_traces[:3]
          ],
          'evaluation_question': 'The response time was acceptable for this type of query',
          'requires_feedback': False,  # Performance is objective, not subjective
          'requires_expectation': False,
        }
      )

    # Check for slow tools
    import re

    slow_tools = {}
    for trace in traces:
      for span in trace.get('data', {}).get('spans', []):
        if span.get('span_type') == 'TOOL':
          raw_tool_name = span.get('name', 'unknown')
          # Normalize tool name by removing _\d+ suffix
          tool_name = re.sub(r'_\d+$', '', raw_tool_name)
          start_ms = span.get('start_time_ms', 0)
          end_ms = span.get('end_time_ms', 0)
          if start_ms and end_ms:
            duration = end_ms - start_ms
            if duration > 5000:  # Tool taking > 5 seconds
              if tool_name not in slow_tools:
                slow_tools[tool_name] = []
              slow_tools[tool_name].append(
                {
                  'trace_id': trace.get('info', {}).get('trace_id'),
                  'duration_ms': duration,
                  'raw_name': raw_tool_name,
                }
              )

    if slow_tools:
      for tool_name, occurrences in slow_tools.items():
        # Get unique raw names for display
        raw_names = list(set(o.get('raw_name', tool_name) for o in occurrences))
        raw_names_str = ', '.join(raw_names[:3]) if len(raw_names) > 1 else tool_name

        issues.append(
          {
            'issue_type': f'slow_tool_{tool_name.replace(" ", "_").lower()}',
            'severity': 'medium',
            'category': 'efficiency',
            'description': f'Tool {tool_name} taking over 5 seconds to execute',
            'why_it_matters': 'Slow tools contribute to overall response latency',
            'total_affected_traces': len(occurrences),
            'all_affected_trace_ids': [o['trace_id'] for o in occurrences],
            'example_snippets': [
              f'Tool {o.get("raw_name", tool_name)}: {o["duration_ms"]}ms in trace {o["trace_id"]}'
              for o in occurrences[:3]
            ],
            'evaluation_question': f'{tool_name} executed efficiently (<5s)',
            'requires_feedback': False,  # Performance is objective, not subjective
            'requires_expectation': False,
          }
        )

    return issues

  def _extract_tool_names(self, trace: Dict[str, Any]) -> List[str]:
    """Extract tool names from trace spans."""
    tools = []
    for span in trace.get('data', {}).get('spans', []):
      if span.get('span_type') == 'TOOL':
        tools.append(span.get('name', 'unknown_tool'))
    return tools

  def _extract_tool_errors(self, trace: Dict[str, Any]) -> List[str]:
    """Extract tool error messages from trace."""
    errors = []
    for span in trace.get('data', {}).get('spans', []):
      if span.get('span_type') == 'TOOL' and span.get('status') == 'ERROR':
        error_msg = span.get('outputs', {}).get('error', '')
        if error_msg:
          errors.append(error_msg[:200])  # Truncate long errors
    return errors

  def _has_errors(self, trace: Dict[str, Any]) -> bool:
    """Check if trace has any errors."""
    return len(self._extract_tool_errors(trace)) > 0
