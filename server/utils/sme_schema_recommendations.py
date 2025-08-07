"""SME Schema Recommendation Utility

This module generates quality-focused labeling schema recommendations based on detected issues
in trace analysis. Schemas are grounded in real trace examples showing quality problems.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SMESchemaRecommender:
  """Generates quality evaluation schemas grounded in actual trace issues."""

  def __init__(self):
    self.logger = logging.getLogger(__name__)

  def recommend_schemas(self, detected_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Recommend labeling schemas based on detected quality issues.

    Args:
        detected_issues: List of quality issues with trace examples

    Returns:
        List of recommended labeling schemas grounded in real issues
    """
    if not detected_issues:
      return self._create_baseline_quality_schemas()

    self.logger.info(
      f'Creating quality-focused schema recommendations for {len(detected_issues)} issues'
    )

    schema_recommendations = []
    seen_schemas = set()

    # Create schemas that directly address quality problems found
    for issue in detected_issues:
      issue_type = issue.get('issue_type', 'unknown')
      severity = issue.get('severity', 'medium')

      # Get example traces showing this issue
      example_traces = issue.get('example_traces', [])
      problem_snippets = issue.get('problem_snippets', [])

      # Create targeted schemas for quality evaluation
      schemas = self._create_quality_schemas_for_issue(issue, example_traces, problem_snippets)

      for schema in schemas:
        if schema['key'] not in seen_schemas:
          seen_schemas.add(schema['key'])
          # Add grounding information
          schema['priority_score'] = self._calculate_priority_score(issue, schema)
          schema['target_issue_type'] = issue_type
          schema['grounded_in_traces'] = example_traces[:3]  # Include trace examples
          schema['addresses_problems'] = problem_snippets[:2]  # Include problem examples
          schema_recommendations.append(schema)

    # Sort by priority score
    schema_recommendations.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

    # Always include overall quality assessment
    if not any(s['key'] == 'overall_quality' for s in schema_recommendations):
      schema_recommendations.extend(self._create_baseline_quality_schemas())

    return schema_recommendations

  def _create_quality_schemas_for_issue(
    self, issue: Dict[str, Any], example_traces: List[str], problem_snippets: List[str]
  ) -> List[Dict[str, Any]]:
    """Create quality evaluation schemas grounded in specific issues."""
    issue_type = issue.get('issue_type', 'unknown')
    severity = issue.get('severity', 'medium')

    # Map quality issues to evaluation schemas with label types
    if 'tool_failure' in issue_type or 'wrong_tool' in issue_type:
      return [
        {
          'key': 'tool_selection_quality',
          'name': 'Tool Selection Quality',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human judgment on tool choice quality
          'min': 1,
          'max': 5,
          'description': 'Evaluate if the correct tools were chosen',
          'evaluation_guidance': 'Rate 1 if completely wrong tool, 5 if perfect choice',
          'rationale': f'Human feedback needed to assess tool selection quality in traces showing: {problem_snippets[0][:100] if problem_snippets else "tool failures"}',
          'categories': None,
        },
        {
          'key': 'correct_tool_expectation',
          'name': 'Expected Tool Usage',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Ground truth of what tool should be used
          'description': 'Specify the correct tool or approach that should have been used',
          'rationale': 'Ground truth needed: agent is using wrong tools, need to specify correct approach for future training',
        },
      ]

    elif 'response_quality' in issue_type or 'faithfulness' in issue_type:
      return [
        {
          'key': 'response_faithfulness',
          'name': 'Response Faithfulness to Tool Outputs',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human evaluation of faithfulness
          'min': 1,
          'max': 5,
          'description': 'Does response accurately reflect tool outputs?',
          'evaluation_guidance': '1=completely fabricated, 5=perfectly faithful',
          'rationale': f'Human feedback needed: agent not reflecting tool errors/outputs correctly as seen in: "{problem_snippets[0][:150] if problem_snippets else "multiple traces"}"',
        },
        {
          'key': 'corrected_response',
          'name': 'Corrected Response',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Ground truth of correct response
          'description': 'Provide the correct response that accurately reflects tool outputs',
          'rationale': 'Ground truth correction needed: agent fabricating information instead of reflecting actual tool outputs',
        },
      ]

    elif 'tone' in issue_type or 'professionalism' in issue_type:
      return [
        {
          'key': 'tone_professionalism',
          'name': 'Tone and Professionalism',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human judgment on tone
          'min': 1,
          'max': 5,
          'description': 'Rate the professionalism of the tone',
          'evaluation_guidance': '1=very unprofessional, 5=perfectly professional',
          'rationale': f'Human feedback on tone issues found: "{problem_snippets[0][:100] if problem_snippets else "unprofessional language detected"}"',
        },
        {
          'key': 'tone_guidelines',
          'name': 'Professional Tone Guidelines',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Guidelines for professional tone
          'description': 'Specify tone requirements (e.g., "must avoid casual language", "should be formal")',
          'rationale': 'Guidelines needed: agent using inappropriate language/tone that needs correction',
        },
      ]

    elif 'logic' in issue_type or 'contradiction' in issue_type:
      return [
        {
          'key': 'logical_consistency',
          'name': 'Logical Consistency',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human evaluation of logic
          'min': 1,
          'max': 5,
          'description': 'Rate the logical coherence and consistency',
          'evaluation_guidance': '1=major contradictions, 5=perfectly logical',
          'rationale': f'Human feedback on logic issues: agent showing contradictions like "{problem_snippets[0][:150] if problem_snippets else "yes/no contradictions"}"',
        },
        {
          'key': 'logical_requirements',
          'name': 'Logical Consistency Requirements',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Requirements for logical consistency
          'description': 'State logical requirements (e.g., "must not contradict previous statements")',
          'rationale': 'Requirements needed: agent violating basic logical consistency principles',
        },
      ]

    elif 'correctness' in issue_type or 'accuracy' in issue_type:
      return [
        {
          'key': 'factual_accuracy',
          'name': 'Factual Accuracy',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human assessment of accuracy
          'min': 1,
          'max': 5,
          'description': 'Rate the factual correctness of the information',
          'evaluation_guidance': '1=mostly wrong, 5=completely accurate',
          'rationale': f'Human verification needed for factual errors like: "{problem_snippets[0][:150] if problem_snippets else "incorrect facts"}"',
        },
        {
          'key': 'correct_facts',
          'name': 'Correct Information',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Ground truth facts
          'description': 'Provide the correct facts and information',
          'rationale': 'Ground truth needed: agent stating incorrect information that needs correction',
        },
      ]

    elif 'completeness' in issue_type:
      return [
        {
          'key': 'response_completeness',
          'name': 'Response Completeness',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human evaluation of completeness
          'min': 1,
          'max': 5,
          'description': 'Rate the completeness of the response',
          'evaluation_guidance': '1=very incomplete, 5=fully complete',
          'rationale': f'Human assessment of incomplete responses: "{problem_snippets[0][:150] if problem_snippets else "truncated/incomplete"}"',
        },
        {
          'key': 'required_information',
          'name': 'Required Information',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # What must be included
          'description': 'List information that must be included for a complete response',
          'rationale': 'Requirements needed: agent missing critical information in responses',
        },
      ]

    elif 'weird' in issue_type or 'strange' in issue_type:
      return [
        {
          'key': 'response_normalcy',
          'name': 'Response Normalcy',
          'schema_type': 'numerical',
          'label_type': 'FEEDBACK',  # Human judgment on normalcy
          'min': 1,
          'max': 5,
          'description': 'Rate how normal and appropriate the response is',
          'evaluation_guidance': '1=very weird/inappropriate, 5=perfectly normal',
          'rationale': f'Human evaluation of weird behaviors: "{problem_snippets[0][:150] if problem_snippets else "unusual patterns"}"',
        },
        {
          'key': 'behavior_expectations',
          'name': 'Expected Behavior Guidelines',
          'schema_type': 'text',
          'label_type': 'EXPECTATION',  # Guidelines for normal behavior
          'description': 'Define expected behavior norms and guidelines',
          'rationale': 'Guidelines needed: agent exhibiting unexpected/weird behaviors that need correction',
        },
      ]

    else:
      # Default quality schemas for other issues
      return self._create_baseline_quality_schemas()

  def _create_baseline_quality_schemas(self) -> List[Dict[str, Any]]:
    """Create baseline quality evaluation schemas."""
    return [
      {
        'key': 'correctness',
        'name': 'Factual Correctness',
        'schema_type': 'numerical',
        'label_type': 'FEEDBACK',  # Human assessment when no specific issues detected
        'min': 1,
        'max': 5,
        'description': 'Rate factual accuracy and correctness of information',
        'evaluation_guidance': '1=mostly wrong, 5=completely accurate',
        'rationale': 'Baseline human feedback needed to assess general correctness when no specific issues detected',
        'target_issue_type': 'baseline_quality',
      },
      {
        'key': 'response_quality',
        'name': 'Overall Response Quality',
        'schema_type': 'numerical',
        'label_type': 'FEEDBACK',  # Human quality assessment
        'min': 1,
        'max': 5,
        'description': 'Rate overall quality including tone, completeness, and usefulness',
        'evaluation_guidance': '1=very poor, 5=excellent',
        'rationale': 'General quality assessment needed when no specific quality issues are detected',
        'target_issue_type': 'baseline_quality',
      },
      {
        'key': 'quality_guidelines',
        'name': 'Quality Requirements',
        'schema_type': 'text',
        'label_type': 'EXPECTATION',  # Guidelines for quality
        'description': 'Define any quality requirements the agent should follow',
        'rationale': 'Capture general quality expectations for the agent behavior',
        'target_issue_type': 'quality_expectations',
      },
    ]

  def _calculate_priority_score(self, issue: Dict[str, Any], schema: Dict[str, Any]) -> int:
    """Calculate priority score for schema based on issue severity and relevance."""
    severity_scores = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25}
    base_score = severity_scores.get(issue.get('severity', 'medium'), 50)

    # Boost score if schema directly addresses the issue
    if schema.get('target_issue_type') == issue.get('issue_type'):
      base_score += 20

    # Boost score if there are many example traces
    example_count = len(issue.get('example_traces', []))
    if example_count > 5:
      base_score += 10

    return min(base_score, 100)  # Cap at 100
