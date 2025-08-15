"""Report Generator Module

Generates comprehensive markdown reports from analysis results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
  """Generates markdown reports from analysis results."""

  def __init__(self):
    """Initialize report generator."""
    self.logger = logging.getLogger(__name__)

  def generate_report(
    self,
    experiment_data: Dict[str, Any],
    discovery_result: Dict[str, Any],
    schemas: List[Dict[str, Any]],
  ) -> str:
    """Generate comprehensive markdown report.

    Args:
        experiment_data: Experiment and trace data
        discovery_result: Issue discovery results
        schemas: Generated evaluation schemas

    Returns:
        Markdown formatted report
    """
    report_sections = []

    # Header
    report_sections.append(self._generate_header(experiment_data))

    # Agent Understanding - MOVED TO TOP
    report_sections.append(self._generate_agent_section(discovery_result))

    # Executive Summary
    report_sections.append(
      self._generate_executive_summary(experiment_data, discovery_result, schemas)
    )

    # Core Metrics
    report_sections.append(self._generate_core_metrics(experiment_data))

    # Tools Analysis
    report_sections.append(self._generate_tools_analysis(experiment_data))

    # Quality Issues
    report_sections.append(self._generate_issues_section(discovery_result))

    # Recommended Schemas - always generate some
    report_sections.append(self._generate_schemas_section(schemas, experiment_data))

    # Actionable Recommendations
    report_sections.append(self._generate_recommendations(discovery_result, experiment_data))

    # Filter out empty sections
    filtered_sections = [section for section in report_sections if section.strip()]
    return '\n\n'.join(filtered_sections)

  def _generate_header(self, experiment_data: Dict[str, Any]) -> str:
    """Generate report header."""
    exp_info = experiment_data['experiment_info']

    return f"""# 🔬 Experiment Analysis Report

**Experiment:** {exp_info['name']} (ID: {exp_info['experiment_id']})  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Method:** Open-Ended Chain-of-Thought Discovery  
**Traces Analyzed:** {experiment_data['total_traces']}"""

  def _generate_executive_summary(
    self,
    experiment_data: Dict[str, Any],
    discovery_result: Dict[str, Any],
    schemas: List[Dict[str, Any]],
  ) -> str:
    """Generate executive summary section."""
    issues = discovery_result['issues']
    critical_count = len([i for i in issues if i['severity'] == 'critical'])
    high_count = len([i for i in issues if i['severity'] == 'high'])

    # Count total affected traces (unique)
    all_affected_traces = set()
    for issue in issues:
      all_affected_traces.update(issue.get('all_trace_ids', []))

    return f"""## 📊 Executive Summary

- **Total Traces Analyzed:** {experiment_data['total_traces']}
- **Traces with Issues:** {len(all_affected_traces)} ({len(all_affected_traces) * 100 // max(experiment_data['total_traces'], 1)}%)
- **Unique Issue Types Found:** {len(issues)}
- **Critical Issues:** {critical_count}
- **High Priority Issues:** {high_count}
- **Evaluation Schemas Generated:** {len(schemas)}

{self._generate_key_findings(experiment_data, issues)}"""

  def _generate_agent_section(self, discovery_result: Dict[str, Any]) -> str:
    """Generate agent understanding section."""
    return f"""## 🤖 Agent Analysis

### What This Agent Does
{discovery_result['agent_understanding']}"""

  def _generate_issues_section(self, discovery_result: Dict[str, Any]) -> str:
    """Generate quality issues section."""
    issues = discovery_result['issues']

    if not issues:
      return '## 🚨 Quality Issues Found\n\nNo significant quality issues detected.'

    sections = ['## 🚨 Quality Issues Found']

    # Group by severity
    for severity in ['critical', 'high', 'medium', 'low']:
      severity_issues = [i for i in issues if i['severity'] == severity]

      if severity_issues:
        severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[severity]

        sections.append(f'\n### {severity_emoji} {severity.title()} Severity Issues')

        for issue in severity_issues:
          sections.append(f"""
#### {issue['title']}

- **Type:** `{issue['issue_type']}`
- **Affected Traces:** {issue['affected_traces']} out of {discovery_result['metadata']['total_traces_analyzed']}
- **Description:** {issue['description']}""")

          if issue.get('problem_snippets'):
            sections.append('\n**Example Problems:**')
            for snippet in issue['problem_snippets'][:2]:
              sections.append(f'```\n{snippet}\n```')

    return '\n'.join(sections)

  def _generate_schemas_section(
    self, schemas: List[Dict[str, Any]], experiment_data: Dict[str, Any] = None
  ) -> str:
    """Generate recommended schemas section."""
    sections = ['## 📋 Recommended Evaluation Schemas']

    # If no schemas from issues, generate default ones
    if not schemas:
      sections.append('\n### Standard Evaluation Criteria')
      sections.append('Consider using these evaluation schemas:')

      # Always suggest some useful schemas
      default_schemas = [
        {
          'name': 'Response Quality',
          'schema_type': 'numerical (1-5)',
          'description': 'Rate the overall quality of the response',
        },
        {
          'name': 'Response Completeness',
          'schema_type': 'categorical (true/false)',
          'description': 'The response fully addressed the user query',
        },
        {
          'name': 'Response Time Acceptable',
          'schema_type': 'categorical (true/false)',
          'description': 'The response time was acceptable for this query',
        },
        {
          'name': 'Additional Feedback',
          'schema_type': 'text',
          'description': 'Any additional observations or issues',
        },
      ]

      for schema in default_schemas:
        sections.append(f"""
📊 **{schema['name']}**  
{schema['schema_type']} - {schema['description']}""")

      return '\n'.join(sections)

    sections = ['## 📋 Recommended Evaluation Schemas']

    # Separate by type
    feedback_schemas = [s for s in schemas if s['label_type'] == 'FEEDBACK']
    expectation_schemas = [s for s in schemas if s['label_type'] == 'EXPECTATION']

    if feedback_schemas:
      sections.append('\n### Human Feedback Schemas')
      sections.append('These schemas require human judgment and evaluation:')

      for schema in feedback_schemas[:5]:  # Top 5
        sections.append(f"""
📊 **{schema['name']}**  
{schema['schema_type']} - {schema['description']}  
Affects {schema.get('affected_trace_count', 0)} traces""")

    if expectation_schemas:
      sections.append('\n### Ground Truth Expectation Schemas')
      sections.append('These schemas capture correct/expected outputs:')

      for schema in expectation_schemas[:5]:  # Top 5
        sections.append(f"""
📝 **{schema['name']}**  
{schema['schema_type']} - {schema['description']}  
Affects {schema.get('affected_trace_count', 0)} traces""")

    return '\n'.join(sections)

  def _generate_detailed_analysis(self, discovery_result: Dict[str, Any]) -> str:
    """Generate detailed analysis section."""
    sections = ['## 🔍 Detailed Analysis']

    # Discovery Process
    sections.append("""
### Discovery Process

This analysis used an open-ended discovery approach:
1. **Agent Understanding**: First analyzed sample traces to understand the agent's purpose and expected behavior
2. **Issue Discovery**: Identified quality issues specific to this agent and domain without using predefined categories
3. **Comprehensive Analysis**: Systematically analyzed all traces for discovered issue patterns
4. **Schema Generation**: Created evaluation schemas tailored to the specific issues found""")

    # Issue Categories Discovered
    categories = discovery_result.get('discovered_categories', [])
    if categories:
      sections.append('\n### Discovered Issue Categories')
      sections.append('The following issue categories were discovered in the data:')

      for i, category in enumerate(categories[:5], 1):
        sections.append(f"""
{i}. **{category.get('issue_name', 'Unknown')}**
   - {category.get('description', 'No description')}
   - Why it matters: {category.get('why_it_matters', 'Impact unknown')}""")

    # Statistics
    issues = discovery_result['issues']
    if issues:
      total_traces = discovery_result['metadata']['total_traces_analyzed']

      sections.append('\n### Issue Distribution')
      sections.append("""
| Severity | Count | Percentage of Issues |
|----------|-------|---------------------|""")

      for severity in ['critical', 'high', 'medium', 'low']:
        count = len([i for i in issues if i['severity'] == severity])
        if count > 0:
          percentage = count * 100 // max(len(issues), 1)
          sections.append(f'| {severity.title()} | {count} | {percentage}% |')

    return '\n'.join(sections)

  def _generate_core_metrics(self, experiment_data: Dict[str, Any]) -> str:
    """Generate core metrics section with latencies, tools, etc."""
    traces = experiment_data['traces']
    if not traces:
      return """## 📊 Core Metrics

**No traces available for analysis**"""

    # Calculate latencies
    latencies = []
    tools_used = set()
    span_types = set()

    for trace in traces:
      # Execution time
      exec_time = trace['info'].get('execution_time_ms')
      if exec_time:
        latencies.append(exec_time)

      # Extract tools and span types from spans
      for span in trace['data']['spans']:
        span_type = span.get('span_type', '')
        if span_type:
          span_types.add(span_type)

        # Extract tool names from span names or inputs
        span_name = span.get('name', '')
        if span_name:
          # Common patterns for tool extraction
          if 'tool' in span_name.lower():
            tools_used.add(span_name)
          elif span_type == 'TOOL':
            tools_used.add(span_name)

    # Calculate stats
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    sections = ['## 📊 Core Metrics']

    sections.append(f"""**Latencies:**
- Average: {avg_latency:.0f}ms
- Range: {min_latency:.0f}ms - {max_latency:.0f}ms""")

    if tools_used:
      tools_list = ', '.join(sorted(list(tools_used))[:5])  # Top 5
      sections.append(f'**Tools Used:** {tools_list}')

    if span_types:
      types_list = ', '.join(sorted(list(span_types)))
      sections.append(f'**Span Types:** {types_list}')

    return '\n\n'.join(sections)

  def _generate_tools_analysis(self, experiment_data: Dict[str, Any]) -> str:
    """Generate tools analysis section."""
    import re

    traces = experiment_data['traces']
    if not traces:
      return ''

    # Collect tool information with normalized names
    tools_info = {}

    for trace in traces:
      for span in trace['data']['spans']:
        if span.get('span_type') == 'TOOL':
          raw_tool_name = span.get('name', 'Unknown Tool')

          # Normalize tool name by removing _\d+ suffix that MLflow adds
          # e.g., execute_sql_query_1 -> execute_sql_query
          normalized_name = re.sub(r'_\d+$', '', raw_tool_name)

          if normalized_name not in tools_info:
            tools_info[normalized_name] = {
              'count': 0,
              'total_duration_ms': 0,
              'min_duration_ms': float('inf'),
              'max_duration_ms': 0,
              'raw_names': set(),  # Track all raw variations
            }

          tools_info[normalized_name]['count'] += 1
          tools_info[normalized_name]['raw_names'].add(raw_tool_name)

          # Calculate duration if available
          start_ms = span.get('start_time_ms', 0)
          end_ms = span.get('end_time_ms', 0)
          if start_ms and end_ms:
            duration = end_ms - start_ms
            tools_info[normalized_name]['total_duration_ms'] += duration
            tools_info[normalized_name]['min_duration_ms'] = min(
              tools_info[normalized_name]['min_duration_ms'], duration
            )
            tools_info[normalized_name]['max_duration_ms'] = max(
              tools_info[normalized_name]['max_duration_ms'], duration
            )

    if not tools_info:
      return ''

    sections = ['## 🔧 Tools Analysis']
    sections.append(
      f'\n**{len(tools_info)} unique tools used across {sum(t["count"] for t in tools_info.values())} invocations**\n'
    )

    # Sort tools by usage count
    sorted_tools = sorted(tools_info.items(), key=lambda x: x[1]['count'], reverse=True)

    for tool_name, info in sorted_tools:
      avg_duration = info['total_duration_ms'] / info['count'] if info['count'] > 0 else 0

      # Show the tool name with variations if they exist
      raw_names = info.get('raw_names', set())
      if len(raw_names) > 1:
        variations_str = f' (includes: {", ".join(sorted(raw_names))})'
      else:
        variations_str = ''

      tool_section = f"""### {tool_name}{variations_str}
- **Invocations**: {info['count']}"""

      if avg_duration > 0:
        tool_section += f"""
- **Avg Duration**: {avg_duration:.0f}ms
- **Duration Range**: {info['min_duration_ms']:.0f}ms - {info['max_duration_ms']:.0f}ms"""

      sections.append(tool_section)

    return '\n\n'.join(sections)

  def _generate_key_findings(
    self, experiment_data: Dict[str, Any], issues: List[Dict[str, Any]]
  ) -> str:
    """Generate key findings callout."""
    traces = experiment_data['traces']
    if not traces or not issues:
      return ''

    # Calculate average latency
    latencies = [
      t['info'].get('execution_time_ms', 0) for t in traces if t['info'].get('execution_time_ms')
    ]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    findings = []

    # Highlight critical performance issue
    if avg_latency > 30000:
      findings.append(
        f'🔴 **CRITICAL:** Average response time is {avg_latency / 1000:.1f}s (3x above 10s threshold)'
      )
    elif avg_latency > 10000:
      findings.append(
        f'🟠 **WARNING:** Average response time is {avg_latency / 1000:.1f}s (above 10s threshold)'
      )

    # Find slowest tool
    slowest_tool = None
    max_tool_duration = 0
    for trace in traces:
      for span in trace['data']['spans']:
        if span.get('span_type') == 'TOOL':
          start_ms = span.get('start_time_ms', 0)
          end_ms = span.get('end_time_ms', 0)
          if start_ms and end_ms:
            duration = end_ms - start_ms
            if duration > max_tool_duration:
              max_tool_duration = duration
              slowest_tool = span.get('name')

    if slowest_tool and max_tool_duration > 10000:
      findings.append(
        f'🔧 **BOTTLENECK:** Tool `{slowest_tool}` took {max_tool_duration / 1000:.1f}s'
      )

    if findings:
      return '### 🎯 Key Findings\n' + '\n'.join(findings)
    return ''

  def _generate_recommendations(
    self, discovery_result: Dict[str, Any], experiment_data: Dict[str, Any]
  ) -> str:
    """Generate actionable recommendations."""
    issues = discovery_result.get('issues', [])
    if not issues:
      return ''

    sections = ['## 💡 Recommendations']

    # Check for performance issues
    has_critical_perf = any(
      i.get('severity') == 'critical' and 'latency' in i.get('issue_type', '') for i in issues
    )
    has_slow_tools = any('slow_tool' in i.get('issue_type', '') for i in issues)

    recommendations = []

    if has_critical_perf:
      recommendations.append(
        '1. **Immediate**: Investigate timeout settings and implement response streaming for long-running operations'
      )
      recommendations.append(
        '2. **Short-term**: Add progress indicators for operations exceeding 5 seconds'
      )
      recommendations.append(
        '3. **Long-term**: Optimize slow database queries and consider caching frequently accessed data'
      )

    if has_slow_tools:
      slow_tool_names = [
        i.get('issue_type', '').replace('slow_tool_', '').replace('_', ' ').title()
        for i in issues
        if 'slow_tool' in i.get('issue_type', '')
      ]
      if slow_tool_names:
        recommendations.append(
          f'4. **Tool Optimization**: Review {", ".join(slow_tool_names[:3])} for performance improvements'
        )

    if not recommendations:
      recommendations.append('1. Continue monitoring performance metrics')
      recommendations.append('2. Set up alerts for response times exceeding 10 seconds')

    sections.extend(recommendations)
    return '\n'.join(sections)

  def _generate_footer(self) -> str:
    """Generate report footer."""
    # Removed - too verbose
    return ''
