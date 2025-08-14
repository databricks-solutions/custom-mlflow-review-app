#!/usr/bin/env python3
"""Analyze labeling session results and provide statistical summaries."""

import argparse
import asyncio
import json
import sys
from collections import Counter, defaultdict
from statistics import mean, median, stdev
from typing import Any, Dict, List, Optional

from server.utils.labeling_items_utils import labeling_items_utils
from server.utils.labeling_sessions_utils import (
  get_labeling_session,
  get_session_by_name,
  list_labeling_sessions,
)
from server.utils.mlflow_utils import get_trace
from tools.utils.review_app_resolver import resolve_review_app_id


def analyze_categorical_schema(items: List[Dict[str, Any]], schema_name: str) -> Dict[str, Any]:
  """Analyze categorical schema results.

  Args:
      items: List of completed labeling items
      schema_name: Name of the schema to analyze

  Returns:
      Dictionary with counts, percentages, and insights
  """
  values = []
  comments = []

  for item in items:
    labels = item.get('labels', {})
    if schema_name in labels:
      value = labels[schema_name]
      if isinstance(value, dict) and 'value' in value:
        values.append(value['value'])
        if 'comment' in value and value['comment']:
          comments.append(value['comment'])
      elif isinstance(value, str):
        values.append(value)

  if not values:
    return {'type': 'categorical', 'total_responses': 0, 'message': 'No responses found'}

  counts = Counter(values)
  total = len(values)

  # Calculate percentages
  percentages = {k: round(v / total * 100, 1) for k, v in counts.items()}

  # Find most common
  most_common = counts.most_common(1)[0] if counts else None

  analysis = {
    'type': 'categorical',
    'total_responses': total,
    'counts': dict(counts),
    'percentages': percentages,
    'most_common': {
      'value': most_common[0],
      'count': most_common[1],
      'percentage': percentages[most_common[0]],
    }
    if most_common
    else None,
    'distribution': [
      {'value': k, 'count': v, 'percentage': percentages[k]} for k, v in counts.most_common()
    ],
    'has_comments': len(comments) > 0,
    'comment_count': len(comments),
  }

  if comments:
    analysis['sample_comments'] = comments[:3]  # Show first 3 comments as examples

  return analysis


def analyze_numeric_schema(items: List[Dict[str, Any]], schema_name: str) -> Dict[str, Any]:
  """Analyze numeric schema results.

  Args:
      items: List of completed labeling items
      schema_name: Name of the schema to analyze

  Returns:
      Dictionary with statistics and insights
  """
  values = []
  comments = []

  for item in items:
    labels = item.get('labels', {})
    if schema_name in labels:
      value = labels[schema_name]
      if isinstance(value, dict) and 'value' in value:
        try:
          numeric_value = float(value['value'])
          values.append(numeric_value)
          if 'comment' in value and value['comment']:
            comments.append(value['comment'])
        except (ValueError, TypeError):
          continue
      elif isinstance(value, (int, float)):
        values.append(float(value))

  if not values:
    return {'type': 'numeric', 'total_responses': 0, 'message': 'No responses found'}

  analysis = {
    'type': 'numeric',
    'total_responses': len(values),
    'mean': round(mean(values), 2),
    'median': round(median(values), 2),
    'min': min(values),
    'max': max(values),
    'has_comments': len(comments) > 0,
    'comment_count': len(comments),
  }

  if len(values) > 1:
    analysis['std_dev'] = round(stdev(values), 2)

  # Create distribution bins
  if len(values) >= 5:
    bins = create_distribution_bins(values)
    analysis['distribution'] = bins

  if comments:
    analysis['sample_comments'] = comments[:3]

  return analysis


def analyze_text_schema(items: List[Dict[str, Any]], schema_name: str) -> Dict[str, Any]:
  """Analyze text schema results.

  Args:
      items: List of completed labeling items
      schema_name: Name of the schema to analyze

  Returns:
      Dictionary with text analysis insights
  """
  texts = []

  for item in items:
    labels = item.get('labels', {})
    if schema_name in labels:
      value = labels[schema_name]
      if isinstance(value, dict) and 'value' in value:
        text = value['value']
        if text and isinstance(text, str):
          texts.append(text.strip())
      elif isinstance(value, str) and value.strip():
        texts.append(value.strip())

  if not texts:
    return {'type': 'text', 'total_responses': 0, 'message': 'No responses found'}

  # Basic text analysis
  total_chars = sum(len(text) for text in texts)
  avg_length = round(total_chars / len(texts), 1)

  # Word frequency analysis (simple)
  all_words = []
  for text in texts:
    words = text.lower().split()
    all_words.extend(words)

  word_counts = Counter(all_words)
  common_words = word_counts.most_common(10)

  analysis = {
    'type': 'text',
    'total_responses': len(texts),
    'avg_length': avg_length,
    'min_length': min(len(text) for text in texts),
    'max_length': max(len(text) for text in texts),
    'total_words': len(all_words),
    'unique_words': len(word_counts),
    'common_words': common_words,
    'sample_responses': texts[:3],  # Show first 3 as examples
  }

  return analysis


def create_distribution_bins(values: List[float], num_bins: int = 5) -> List[Dict[str, Any]]:
  """Create distribution bins for numeric values.

  Args:
      values: List of numeric values
      num_bins: Number of bins to create

  Returns:
      List of bin dictionaries with range and count
  """
  if not values:
    return []

  min_val = min(values)
  max_val = max(values)

  if min_val == max_val:
    return [{'range': f'{min_val}', 'count': len(values), 'percentage': 100.0}]

  bin_width = (max_val - min_val) / num_bins
  bins = []

  for i in range(num_bins):
    bin_start = min_val + i * bin_width
    bin_end = bin_start + bin_width

    if i == num_bins - 1:  # Last bin includes max value
      count = sum(1 for v in values if bin_start <= v <= bin_end)
    else:
      count = sum(1 for v in values if bin_start <= v < bin_end)

    percentage = round(count / len(values) * 100, 1)

    bins.append(
      {'range': f'{bin_start:.1f}-{bin_end:.1f}', 'count': count, 'percentage': percentage}
    )

  return bins


async def get_trace_content(trace_id: str) -> Optional[Dict[str, Any]]:
  """Get trace content for analysis.

  Args:
      trace_id: The trace ID to fetch

  Returns:
      Dictionary with trace content or None if not found
  """
  try:
    raw_trace = get_trace(trace_id)
    # Use built-in to_dict() for conversion
    trace_dict = raw_trace.to_dict()

    # Convert to expected format for compatibility
    trace_info = trace_dict.get('info', {})
    trace_data = {
      'info': {
        'trace_id': trace_info.get('trace_id', trace_info.get('request_id', '')),
        'experiment_id': trace_info.get('experiment_id', ''),
        'assessments': [],  # Will be populated if assessments exist
        'execution_duration': f'{trace_info.get("execution_time_ms", 0)}ms',
      }
    }

    # Convert assessments if present
    if hasattr(raw_trace.info, 'assessments') and raw_trace.info.assessments:
      for assessment in raw_trace.info.assessments:
        assessment_dict = {}
        if hasattr(assessment, 'name'):
          assessment_dict['name'] = assessment.name
        if hasattr(assessment, 'value'):
          assessment_dict['value'] = assessment.value
        elif hasattr(assessment, 'feedback') and assessment.feedback:
          assessment_dict['value'] = assessment.feedback.value
        elif hasattr(assessment, 'expectation') and assessment.expectation:
          assessment_dict['value'] = assessment.expectation.value

        if 'name' in assessment_dict and 'value' in assessment_dict:
          trace_data['info']['assessments'].append(assessment_dict)

    return trace_data
  except Exception as e:
    print(f'Warning: Could not fetch trace {trace_id}: {str(e)}', file=sys.stderr)
    return None


def extract_trace_patterns(trace_data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract patterns from trace content for correlation analysis.

  Args:
      trace_data: Raw trace data from MLflow

  Returns:
      Dictionary with extracted patterns
  """
  patterns = {
    'input_length': 0,
    'output_length': 0,
    'execution_time_ms': 0,
    'status': 'UNKNOWN',
    'error_present': False,
    'input_keywords': [],
    'output_keywords': [],
    'tool_usage': [],
    'conversation_turns': 0,
  }

  try:
    trace_info = trace_data.get('info', {})
    patterns['execution_time_ms'] = trace_info.get('execution_time_ms', 0)
    patterns['status'] = trace_info.get('status', 'UNKNOWN')

    # Analyze trace data
    data = trace_data.get('data', {})

    # Extract input/output from spans
    spans = data.get('spans', [])
    for span in spans:
      span_data = span.get('inputs', {})
      span_outputs = span.get('outputs', {})

      # Look for common input fields
      for key in ['input', 'prompt', 'question', 'query', 'request']:
        if key in span_data:
          content = str(span_data[key])
          patterns['input_length'] = max(patterns['input_length'], len(content))
          # Extract keywords (simple approach)
          words = content.lower().split()
          patterns['input_keywords'].extend([w for w in words if len(w) > 3])

      # Look for common output fields
      for key in ['output', 'response', 'answer', 'result']:
        if key in span_outputs:
          content = str(span_outputs[key])
          patterns['output_length'] = max(patterns['output_length'], len(content))
          words = content.lower().split()
          patterns['output_keywords'].extend([w for w in words if len(w) > 3])

      # Check for errors
      if span.get('status_code') == 'ERROR' or 'error' in str(span_outputs).lower():
        patterns['error_present'] = True

      # Count conversation turns
      if span.get('span_type') == 'CHAT':
        patterns['conversation_turns'] += 1

    # Get most common keywords (top 5)
    patterns['input_keywords'] = [
      word for word, _ in Counter(patterns['input_keywords']).most_common(5)
    ]
    patterns['output_keywords'] = [
      word for word, _ in Counter(patterns['output_keywords']).most_common(5)
    ]

  except Exception as e:
    print(f'Warning: Error extracting trace patterns: {str(e)}', file=sys.stderr)

  return patterns


def correlate_assessments_with_traces(
  items: List[Dict[str, Any]], trace_patterns: Dict[str, Dict[str, Any]], schema_name: str
) -> Dict[str, Any]:
  """Correlate SME assessments with trace content patterns.

  Args:
      items: List of completed labeling items with assessments
      trace_patterns: Dictionary mapping trace_id to extracted patterns
      schema_name: Name of the assessment schema

  Returns:
      Dictionary with correlation analysis
  """
  correlations = {
    'total_analyzed': 0,
    'patterns_by_rating': defaultdict(list),
    'common_patterns': {},
    'insights': [],
  }

  try:
    for item in items:
      labels = item.get('labels', {})
      if schema_name not in labels:
        continue

      # Get the assessment value
      assessment = labels[schema_name]
      assessment_value = None

      if isinstance(assessment, dict) and 'value' in assessment:
        assessment_value = assessment['value']
      elif isinstance(assessment, (str, int, float)):
        assessment_value = assessment

      if assessment_value is None:
        continue

      # Get trace ID from item source
      source = item.get('source', {})
      trace_id = source.get('trace_id')

      if trace_id and trace_id in trace_patterns:
        patterns = trace_patterns[trace_id]
        correlations['patterns_by_rating'][str(assessment_value)].append(patterns)
        correlations['total_analyzed'] += 1

    # Analyze patterns by rating
    for rating, pattern_list in correlations['patterns_by_rating'].items():
      if not pattern_list:
        continue

      # Calculate averages for numeric patterns
      avg_input_length = mean([p['input_length'] for p in pattern_list if p['input_length'] > 0])
      avg_output_length = mean([p['output_length'] for p in pattern_list if p['output_length'] > 0])
      avg_execution_time = mean(
        [p['execution_time_ms'] for p in pattern_list if p['execution_time_ms'] > 0]
      )

      # Count common keywords
      all_input_keywords = []
      all_output_keywords = []
      for p in pattern_list:
        all_input_keywords.extend(p['input_keywords'])
        all_output_keywords.extend(p['output_keywords'])

      common_input_keywords = [word for word, _ in Counter(all_input_keywords).most_common(3)]
      common_output_keywords = [word for word, _ in Counter(all_output_keywords).most_common(3)]

      # Error rate
      error_rate = sum(1 for p in pattern_list if p['error_present']) / len(pattern_list) * 100

      correlations['common_patterns'][rating] = {
        'count': len(pattern_list),
        'avg_input_length': round(avg_input_length, 1) if avg_input_length else 0,
        'avg_output_length': round(avg_output_length, 1) if avg_output_length else 0,
        'avg_execution_time_ms': round(avg_execution_time, 1) if avg_execution_time else 0,
        'error_rate': round(error_rate, 1),
        'common_input_keywords': common_input_keywords,
        'common_output_keywords': common_output_keywords,
      }

    # Generate insights
    if len(correlations['common_patterns']) > 1:
      ratings = list(correlations['common_patterns'].keys())

      # Compare high vs low ratings (if numeric-like)
      try:
        numeric_ratings = [
          (float(r), r) for r in ratings if r.replace('.', '').replace('-', '').isdigit()
        ]
        if len(numeric_ratings) >= 2:
          numeric_ratings.sort()
          low_rating = numeric_ratings[0][1]
          high_rating = numeric_ratings[-1][1]

          low_patterns = correlations['common_patterns'][low_rating]
          high_patterns = correlations['common_patterns'][high_rating]

          # Compare patterns
          if high_patterns['avg_execution_time_ms'] > low_patterns['avg_execution_time_ms'] * 1.5:
            correlations['insights'].append(
              f'Higher-rated responses took {high_patterns["avg_execution_time_ms"]:.0f}ms vs '
              f'{low_patterns["avg_execution_time_ms"]:.0f}ms - longer processing time correlates with better ratings'
            )

          if low_patterns['error_rate'] > high_patterns['error_rate'] * 2:
            correlations['insights'].append(
              f'Lower-rated responses had {low_patterns["error_rate"]:.1f}% error rate vs '
              f'{high_patterns["error_rate"]:.1f}% - errors correlate with poor ratings'
            )

          if high_patterns['avg_output_length'] > low_patterns['avg_output_length'] * 1.3:
            correlations['insights'].append(
              f'Higher-rated responses were longer ({high_patterns["avg_output_length"]:.0f} vs '
              f'{low_patterns["avg_output_length"]:.0f} chars) - detail correlates with quality'
            )

      except Exception:
        pass  # Skip numeric comparison if ratings aren't numeric

  except Exception as e:
    print(f'Warning: Error in correlation analysis: {str(e)}', file=sys.stderr)

  return correlations


def generate_insights(session_analysis: Dict[str, Any]) -> List[str]:
  """Generate insights from session analysis.

  Args:
      session_analysis: Analysis results for a session

  Returns:
      List of insight strings
  """
  insights = []

  # Overall completion insights
  if session_analysis.get('completion_rate', 0) < 50:
    insights.append('⚠️ Low completion rate - consider session complexity or SME availability')
  elif session_analysis.get('completion_rate', 0) > 90:
    insights.append('✅ Excellent completion rate - high SME engagement')

  # Schema-specific insights
  schema_results = session_analysis.get('schema_analysis', {})

  for schema_name, analysis in schema_results.items():
    if analysis['type'] == 'categorical':
      if analysis.get('total_responses', 0) > 0:
        most_common = analysis.get('most_common')
        if most_common and most_common['percentage'] > 80:
          insights.append(
            f"📊 {schema_name}: Strong consensus ({most_common['percentage']}% chose '"
            f"{most_common['value']}')"
          )
        elif most_common and most_common['percentage'] < 40:
          insights.append(f'🤔 {schema_name}: Diverse opinions - no clear consensus')

    elif analysis['type'] == 'numeric':
      if analysis.get('total_responses', 0) > 0:
        mean_val = analysis.get('mean', 0)
        if mean_val >= 4.0:  # Assuming 5-point scale
          insights.append(f'⭐ {schema_name}: High ratings (avg: {mean_val})')
        elif mean_val <= 2.0:
          insights.append(f'⚠️ {schema_name}: Low ratings (avg: {mean_val}) - needs attention')

        std_dev = analysis.get('std_dev', 0)
        if std_dev and std_dev > 1.0:
          insights.append(f'📈 {schema_name}: High variance in ratings - mixed opinions')

    elif analysis['type'] == 'text':
      if analysis.get('total_responses', 0) > 0:
        avg_length = analysis.get('avg_length', 0)
        if avg_length > 100:
          insights.append(f'📝 {schema_name}: Detailed feedback (avg: {avg_length:.0f} chars)')
        elif avg_length < 20:
          insights.append(f'💬 {schema_name}: Brief responses - consider more specific prompts')

  return insights


async def analyze_session(
  review_app_id: str, session_id: str, session_name: str, schemas: List[Dict[str, Any]]
) -> Dict[str, Any]:
  """Analyze a single labeling session with trace content correlation.

  Args:
      review_app_id: Review app ID
      session_id: Labeling session ID
      session_name: Session name for display
      schemas: List of schema definitions

  Returns:
      Dictionary with analysis results including trace correlations
  """
  try:
    # Get all items for this session
    items_response = await labeling_items_utils.list_items(
      review_app_id=review_app_id, labeling_session_id=session_id
    )

    items = items_response.get('items', [])
    completed_items = [item for item in items if item.get('state') == 'COMPLETED']

    if not completed_items:
      return {
        'session_name': session_name,
        'total_items': len(items),
        'completed_items': 0,
        'completion_rate': 0.0,
        'message': 'No completed items to analyze',
      }

    # Fetch trace content for correlation analysis
    trace_patterns = {}
    unique_trace_ids = set()

    # Get all trace IDs from items
    for item in items:
      source = item.get('source', {})
      trace_id = source.get('trace_id')
      if trace_id:
        unique_trace_ids.add(trace_id)

    # Fetch trace content and extract patterns
    for trace_id in unique_trace_ids:
      trace_data = await get_trace_content(trace_id)
      if trace_data:
        patterns = extract_trace_patterns(trace_data)
        trace_patterns[trace_id] = patterns

    # Analyze each schema with trace correlation
    schema_analysis = {}
    for schema in schemas:
      schema_name = schema.get('name')
      if not schema_name:
        continue

      # Determine schema type from structure and analyze
      if schema.get('categorical') or schema.get('categorical_list'):
        analysis = analyze_categorical_schema(completed_items, schema_name)
      elif schema.get('numeric'):
        analysis = analyze_numeric_schema(completed_items, schema_name)
      elif schema.get('text') or schema.get('text_list'):
        analysis = analyze_text_schema(completed_items, schema_name)
      else:
        continue

      # Add trace correlation analysis if we have completed items
      if analysis.get('total_responses', 0) > 0 and trace_patterns:
        correlation_analysis = correlate_assessments_with_traces(
          completed_items, trace_patterns, schema_name
        )
        analysis['trace_correlation'] = correlation_analysis

      schema_analysis[schema_name] = analysis

    completion_rate = round(len(completed_items) / len(items) * 100, 1) if items else 0.0

    session_analysis = {
      'session_name': session_name,
      'session_id': session_id,
      'total_items': len(items),
      'completed_items': len(completed_items),
      'completion_rate': completion_rate,
      'traces_analyzed': len(trace_patterns),
      'schema_analysis': schema_analysis,
    }

    # Generate insights including trace correlations
    insights = generate_insights(session_analysis)
    session_analysis['insights'] = insights

    return session_analysis

  except Exception as e:
    return {'session_name': session_name, 'session_id': session_id, 'error': str(e)}


def format_analysis_output(analysis_results: List[Dict[str, Any]]) -> str:
  """Format analysis results for CLI output with assessment-oriented reporting.

  Args:
      analysis_results: List of session analysis results

  Returns:
      Formatted string for CLI display
  """
  output = []
  output.append('# 📊 Complete Labeling Results Analysis System\n')

  # Overall summary first
  total_sessions = len(analysis_results)
  total_items = sum(r.get('total_items', 0) for r in analysis_results)
  total_completed = sum(r.get('completed_items', 0) for r in analysis_results)
  overall_completion = round(total_completed / total_items * 100, 1) if total_items > 0 else 0

  output.append('## 🎯 Overall Summary')
  output.append(f'**Sessions**: {total_sessions}')
  output.append(f'**Total Items**: {total_items}')
  output.append(f'**Completed**: {total_completed} ({overall_completion}%)')
  output.append('')

  for i, result in enumerate(analysis_results, 1):
    if 'error' in result:
      output.append(f'## {i}. ❌ {result["session_name"]}')
      output.append(f'**Error**: {result["error"]}\n')
      continue

    session_name = result.get('session_name', 'Unknown Session')
    completion_rate = result.get('completion_rate', 0)
    completed = result.get('completed_items', 0)
    total = result.get('total_items', 0)
    traces_analyzed = result.get('traces_analyzed', 0)

    output.append(f'## {i}. 📋 {session_name}')
    output.append(f'**Progress**: {completed}/{total} items completed ({completion_rate}%)')
    if traces_analyzed > 0:
      output.append(f'**Trace Analysis**: {traces_analyzed} traces analyzed for patterns')

    if 'message' in result:
      output.append(f'**Status**: {result["message"]}\n')
      continue

    # Assessment-oriented analysis
    schema_analysis = result.get('schema_analysis', {})
    if schema_analysis:
      output.append('\n### 📈 Assessment Analysis:')

      for schema_name, analysis in schema_analysis.items():
        output.append(f'\n#### 🎯 {schema_name.title()} Assessment')

        if analysis['type'] == 'categorical':
          if analysis.get('total_responses', 0) > 0:
            output.append(f'**SME Responses**: {analysis["total_responses"]}')
            distribution = analysis.get('distribution', [])

            # Show distribution with visual bars
            output.append('**Distribution**:')
            for item in distribution:
              bar_length = int(item['percentage'] / 5)  # Scale for display
              bar = '█' * bar_length
              output.append(f'  {item["value"]}: {item["count"]} ({item["percentage"]}%) {bar}')

            # Most common consensus
            most_common = analysis.get('most_common')
            if most_common:
              output.append(
                f"**Consensus**: {most_common['percentage']}% chose '{most_common['value']}'"
              )

          else:
            output.append('**No SME responses yet**')

        elif analysis['type'] == 'numeric':
          if analysis.get('total_responses', 0) > 0:
            output.append(f'**SME Responses**: {analysis["total_responses"]}')
            output.append(f'**Average Rating**: {analysis["mean"]}/5.0')
            output.append(f'**Rating Range**: {analysis["min"]} - {analysis["max"]}')
            output.append(f'**Median**: {analysis["median"]}')
            if 'std_dev' in analysis:
              variance_level = 'High' if analysis['std_dev'] > 1.0 else 'Low'
              output.append(f'**Variance**: {analysis["std_dev"]} ({variance_level})')

            # Distribution bins if available
            distribution = analysis.get('distribution', [])
            if distribution:
              output.append('**Rating Distribution**:')
              for bin_data in distribution:
                if bin_data['count'] > 0:
                  bar_length = int(bin_data['percentage'] / 5)
                  bar = '█' * bar_length
                  output.append(
                    f'  {bin_data["range"]}: {bin_data["count"]} ({bin_data["percentage"]}%) {bar}'
                  )
          else:
            output.append('**No SME ratings yet**')

        elif analysis['type'] == 'text':
          if analysis.get('total_responses', 0) > 0:
            output.append(f'**SME Feedback**: {analysis["total_responses"]} responses')
            output.append(f'**Avg Length**: {analysis["avg_length"]} characters')
            output.append(
              f'**Detail Level**: {"Detailed" if analysis["avg_length"] > 50 else "Brief"}'
            )

            # Show common themes if available
            common_words = analysis.get('common_words', [])
            if common_words:
              top_themes = [word for word, count in common_words[:5] if count > 1]
              if top_themes:
                output.append(f'**Common Themes**: {", ".join(top_themes)}')

            # Sample responses
            samples = analysis.get('sample_responses', [])
            if samples:
              output.append('**Sample Feedback**:')
              for sample in samples[:2]:  # Show 2 samples
                preview = sample[:100] + '...' if len(sample) > 100 else sample
                output.append(f'  • "{preview}"')
          else:
            output.append('**No SME feedback yet**')

        # Trace correlation analysis
        trace_correlation = analysis.get('trace_correlation', {})
        if trace_correlation and trace_correlation.get('total_analyzed', 0) > 0:
          output.append(
            f'\n**🔍 Trace Pattern Analysis** ({trace_correlation["total_analyzed"]} traces)'
          )

          common_patterns = trace_correlation.get('common_patterns', {})
          if common_patterns:
            output.append('**Patterns by Rating**:')
            for rating, patterns in common_patterns.items():
              output.append(f'  **{rating}** ({patterns["count"]} traces):')
              if patterns['avg_execution_time_ms'] > 0:
                output.append(f'    • Avg processing: {patterns["avg_execution_time_ms"]:.0f}ms')
              if patterns['avg_output_length'] > 0:
                output.append(
                  f'    • Avg response length: {patterns["avg_output_length"]:.0f} chars'
                )
              if patterns['error_rate'] > 0:
                output.append(f'    • Error rate: {patterns["error_rate"]:.1f}%')
              if patterns['common_output_keywords']:
                keywords = ', '.join(patterns['common_output_keywords'][:3])
                output.append(f'    • Common themes: {keywords}')

          # Correlation insights
          correlation_insights = trace_correlation.get('insights', [])
          if correlation_insights:
            output.append('**🎯 Pattern Insights**:')
            for insight in correlation_insights:
              output.append(f'  • {insight}')

    # Overall session insights
    insights = result.get('insights', [])
    if insights:
      output.append('\n### 💡 Key Session Insights:')
      for insight in insights:
        output.append(f'  • {insight}')

    output.append('')  # Add spacing between sessions

  return '\n'.join(output)


async def main():
  """Main function to analyze labeling results."""
  parser = argparse.ArgumentParser(
    description='Analyze labeling session results and provide statistical summaries'
  )
  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('--session-id', help='Specific session ID to analyze (optional)')
  parser.add_argument('--session-name', help='Specific session name to analyze (optional)')
  parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
  parser.add_argument('--filter', help='Filter sessions (e.g., state=COMPLETED)')

  args = parser.parse_args()

  try:
    # Resolve review app ID and get review app to access schema definitions
    review_app_id, review_app = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )
    all_schemas = review_app.get('labeling_schemas', []) if review_app else []

    # Get sessions to analyze
    if args.session_id:
      # Analyze specific session
      session = await get_labeling_session(
        review_app_id=review_app_id, labeling_session_id=args.session_id
      )
      sessions_to_analyze = [session]
    elif args.session_name:
      # Find session by name
      session = await get_session_by_name(
        review_app_id=review_app_id, session_name=args.session_name
      )
      if not session:
        print(f"❌ Session '{args.session_name}' not found", file=sys.stderr)
        sys.exit(1)
      sessions_to_analyze = [session]
    else:
      # Get all sessions
      sessions_response = await list_labeling_sessions(
        review_app_id=review_app_id, filter_string=args.filter
      )
      sessions_to_analyze = (
        sessions_response.get('labeling_sessions', []) if sessions_response else []
      )

    if not sessions_to_analyze:
      print('❌ No sessions found to analyze', file=sys.stderr)
      sys.exit(1)

    # Analyze each session
    analysis_results = []
    for session in sessions_to_analyze:
      session_id = session.get('labeling_session_id')
      session_name = session.get('name', f'Session {session_id}')

      # Get schemas for this session
      session_schema_refs = session.get('labeling_schemas', [])
      session_schema_names = {ref.get('name') for ref in session_schema_refs}
      session_schemas = [
        schema for schema in all_schemas if schema.get('name') in session_schema_names
      ]

      result = await analyze_session(review_app_id, session_id, session_name, session_schemas)
      analysis_results.append(result)

    # Output results
    if args.format == 'json':
      print(json.dumps(analysis_results, indent=2, default=str))
    else:
      formatted_output = format_analysis_output(analysis_results)
      print(formatted_output)

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
