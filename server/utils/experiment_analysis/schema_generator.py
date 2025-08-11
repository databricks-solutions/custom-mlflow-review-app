"""Dynamic Schema Generator Module

Generates evaluation schemas based on discovered issues.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SchemaGenerator:
  """Generates evaluation schemas dynamically based on discovered issues."""

  def __init__(self):
    """Initialize schema generator."""
    self.logger = logging.getLogger(__name__)

  def generate_schemas_for_issues(
    self, issues: List[Dict[str, Any]], agent_understanding: str
  ) -> List[Dict[str, Any]]:
    """Generate evaluation schemas based on discovered issues.

    Args:
        issues: List of discovered issues with trace mappings
        agent_understanding: Context about what the agent does

    Returns:
        List of evaluation schemas ready for SME use
    """
    schemas = []

    # Skip performance issues for human feedback - those are objective metrics
    # Filter out performance-related issues as they don't need human judgment
    subjective_issues = [
      i
      for i in issues
      if i.get('category') != 'performance' and 'latency' not in i.get('issue_type', '').lower()
    ]

    for issue in subjective_issues:
      # Generate schemas based on issue characteristics
      if issue.get('requires_feedback'):
        feedback_schema = self._create_feedback_schema(issue)
        if feedback_schema:
          schemas.append(feedback_schema)

      if issue.get('requires_expectation'):
        expectation_schema = self._create_expectation_schema(issue)
        if expectation_schema:
          schemas.append(expectation_schema)

    # Deduplicate and prioritize
    schemas = self._deduplicate_schemas(schemas)
    schemas = self._prioritize_schemas(schemas, issues)

    # Add domain-specific SUBJECTIVE schemas for Databricks agents
    if 'databricks' in agent_understanding.lower() or 'warehouse' in agent_understanding.lower():
      schemas.extend(
        [
          {
            'key': 'response_faithful_to_tools',
            'name': 'Response Faithful to Tool Outputs',
            'label_type': 'FEEDBACK',
            'schema_type': 'categorical',
            'description': 'The agent accurately summarized tool outputs without hallucination',
            'rationale': 'Ensures agent responses are grounded in actual tool results',
            'priority_score': 95,
            'affected_trace_count': len(issues),
            'all_affected_traces': [],
          },
          {
            'key': 'query_understanding',
            'name': 'Query Understanding',
            'label_type': 'FEEDBACK',
            'schema_type': 'categorical',
            'description': "The agent correctly understood the user's intent and request",
            'rationale': 'Misunderstanding user intent leads to incorrect tool usage',
            'priority_score': 90,
            'affected_trace_count': 0,
            'all_affected_traces': [],
          },
          {
            'key': 'response_completeness',
            'name': 'Response Completeness',
            'label_type': 'FEEDBACK',
            'schema_type': 'categorical',
            'description': "The agent provided all necessary information to answer the user's question",
            'rationale': 'Incomplete responses require follow-up questions',
            'priority_score': 85,
            'affected_trace_count': 0,
            'all_affected_traces': [],
          },
          {
            'key': 'unnecessary_tool_calls',
            'name': 'Tool Usage Efficiency',
            'label_type': 'FEEDBACK',
            'schema_type': 'categorical',
            'description': 'The agent avoided unnecessary or redundant tool calls',
            'rationale': 'Excessive tool usage wastes resources and increases latency',
            'priority_score': 80,
            'affected_trace_count': 0,
            'all_affected_traces': [],
          },
          {
            'key': 'error_explanation',
            'name': 'Error Communication',
            'label_type': 'FEEDBACK',
            'schema_type': 'categorical',
            'description': 'When errors occurred, the agent explained them clearly to the user',
            'rationale': 'Clear error communication helps users understand and resolve issues',
            'priority_score': 75,
            'affected_trace_count': 0,
            'all_affected_traces': [],
          },
        ]
      )

    # Only add generic baseline schemas if we have very few specific ones
    if len(schemas) < 3:
      schemas.extend(self._create_baseline_schemas(agent_understanding))

    return schemas

  def _create_feedback_schema(self, issue: Dict[str, Any]) -> Dict[str, Any]:
    """Create a feedback (human judgment) schema for an issue."""
    # Determine schema type based on evaluation question
    schema_type = self._infer_schema_type(issue.get('evaluation_question', ''))

    # Adjust the question for categorical (true/false) schemas
    description = issue.get('evaluation_question', '')
    if schema_type == 'categorical':
      # Rephrase as a statement that can be true/false
      if not description.startswith(('Is ', 'Does ', 'Was ', 'Has ', 'Are ')):
        # Convert to a true/false statement
        description = self._convert_to_true_false_statement(description, issue)

    schema = {
      'key': self._sanitize_key(issue['issue_type']),
      'name': issue.get('title', issue['issue_type'].replace('_', ' ').title()),
      'label_type': 'FEEDBACK',
      'schema_type': schema_type,
      'description': description,
      'rationale': f"Human evaluation needed: {issue.get('description', '')}",
      'priority_score': self._calculate_priority(issue),
      'grounded_in_traces': issue.get('example_traces', [])[:3],
      'all_affected_traces': issue.get('all_trace_ids', []),
      'affected_trace_count': issue.get('affected_traces', 0),
    }

    # Add type-specific fields
    if schema_type == 'numerical':
      schema.update(
        {'min': 1, 'max': 5, 'evaluation_guidance': self._generate_rating_guidance(issue)}
      )
    elif schema_type == 'categorical':
      schema.update(
        {
          'options': self._generate_categorical_options(issue),
          'enable_comment': True,  # Always enable comments for true/false
          'comment_required': False,  # Optional but encouraged
          'comment_placeholder': 'Please explain your choice (optional but helpful)',
        }
      )
    elif schema_type == 'text':
      schema.update(
        {
          'max_length': 500,
          'placeholder': 'Provide detailed feedback...',
          'enable_comment': False,  # Text is already a comment
        }
      )

    return schema

  def _create_expectation_schema(self, issue: Dict[str, Any]) -> Dict[str, Any]:
    """Create an expectation (ground truth) schema for an issue."""
    schema = {
      'key': f"{self._sanitize_key(issue['issue_type'])}_expectation",
      'name': f"Expected: {issue.get('title', issue['issue_type'].replace('_', ' ').title())}",
      'label_type': 'EXPECTATION',
      'schema_type': 'text',  # Expectations are usually text corrections
      'description': self._generate_expectation_question(issue),
      'rationale': f"Ground truth needed: {issue.get('description', '')}",
      'priority_score': self._calculate_priority(issue),
      'grounded_in_traces': issue.get('example_traces', [])[:3],
      'all_affected_traces': issue.get('all_trace_ids', []),
      'affected_trace_count': issue.get('affected_traces', 0),
      'max_length': 1000,
      'placeholder': 'Provide the correct/expected response...',
      'enable_comment': True,
    }

    return schema

  def _infer_schema_type(self, evaluation_question: str) -> str:
    """Infer the appropriate schema type from the evaluation question."""
    question_lower = evaluation_question.lower()

    # Check for correction/rewrite indicators FIRST (for text)
    text_keywords = ['rewrite', 'provide', 'what should', 'explain', 'describe', 'write']
    if any(keyword in question_lower for keyword in text_keywords):
      return 'text'

    # Check for rating/scoring indicators (less preferred)
    rating_keywords = ['rate', 'score', 'scale', 'level', '1-5', '1-10']
    if any(keyword in question_lower for keyword in rating_keywords):
      return 'numerical'

    # Default to categorical (true/false, yes/no) for most feedback
    # This encourages binary decisions which are easier for SMEs
    return 'categorical'

  def _generate_rating_guidance(self, issue: Dict[str, Any]) -> str:
    """Generate guidance for numerical ratings."""
    severity = issue.get('severity', 'medium')

    if severity == 'critical':
      return '1=Completely wrong/broken, 3=Partially correct, 5=Perfect'
    elif severity == 'high':
      return '1=Major issues, 3=Some problems, 5=Excellent'
    else:
      return '1=Poor, 3=Acceptable, 5=Excellent'

  def _generate_categorical_options(self, issue: Dict[str, Any]) -> List[str]:
    """Generate appropriate categorical options based on issue type."""
    issue_type = issue.get('issue_type', '').lower()

    # Prefer simple true/false for most cases
    if 'partial' in issue_type or 'degree' in issue_type:
      # Only use multiple options when explicitly about degrees
      if 'correct' in issue_type or 'accurate' in issue_type:
        return ['Correct', 'Partially Correct', 'Incorrect']
      elif 'complete' in issue_type:
        return ['Complete', 'Partially Complete', 'Incomplete']
      else:
        return ['Yes', 'Somewhat', 'No']
    else:
      # Default to simple binary choice for easier SME decisions
      return ['True', 'False']

  def _convert_to_true_false_statement(self, question: str, issue: Dict[str, Any]) -> str:
    """Convert a question to a true/false statement."""
    # Common conversions
    conversions = {
      'how well': 'The response handles this well',
      'quality': 'The response quality is acceptable',
      'correct': 'The response is correct',
      'accurate': 'The response is accurate',
      'appropriate': 'The response is appropriate',
      'complete': 'The response is complete',
      'professional': 'The response is professional',
      'helpful': 'The response is helpful',
    }

    question_lower = question.lower()
    for key, statement in conversions.items():
      if key in question_lower:
        return statement

    # Default: Convert to "Is/Does..." if not already
    if not question.startswith(('Is ', 'Does ', 'Was ', 'Has ', 'Are ')):
      return f"The {issue.get('title', 'response').lower()} is acceptable"

    return question

  def _generate_expectation_question(self, issue: Dict[str, Any]) -> str:
    """Generate an appropriate expectation question."""
    issue_type = issue.get('issue_type', '').lower()

    if 'response' in issue_type or 'output' in issue_type:
      return 'Provide the correct response that should have been given'
    elif 'tool' in issue_type:
      return 'Specify which tool should have been used and how'
    elif 'information' in issue_type or 'fact' in issue_type:
      return 'Provide the correct information or facts'
    elif 'behavior' in issue_type:
      return 'Describe the expected behavior'
    else:
      return 'Provide the correct or expected output for this case'

  def _calculate_priority(self, issue: Dict[str, Any]) -> int:
    """Calculate priority score based on severity and affected traces."""
    severity_scores = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25}

    base_score = severity_scores.get(issue.get('severity', 'medium'), 50)

    # Boost score based on number of affected traces
    affected_traces = issue.get('affected_traces', 0)
    if affected_traces > 20:
      base_score += 20
    elif affected_traces > 10:
      base_score += 10
    elif affected_traces > 5:
      base_score += 5

    return min(base_score, 100)  # Cap at 100

  def _sanitize_key(self, issue_type: str) -> str:
    """Create a valid schema key from issue type."""
    # Remove special characters and convert to snake_case
    key = issue_type.lower()
    key = ''.join(c if c.isalnum() or c == '_' else '_' for c in key)
    key = '_'.join(filter(None, key.split('_')))  # Remove multiple underscores

    return key[:50]  # Limit length

  def _deduplicate_schemas(self, schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate schemas based on key."""
    seen_keys = set()
    unique_schemas = []

    for schema in schemas:
      if schema['key'] not in seen_keys:
        seen_keys.add(schema['key'])
        unique_schemas.append(schema)
      else:
        # Merge trace IDs if duplicate
        for existing in unique_schemas:
          if existing['key'] == schema['key']:
            existing_traces = set(existing.get('all_affected_traces', []))
            new_traces = set(schema.get('all_affected_traces', []))
            existing['all_affected_traces'] = list(existing_traces | new_traces)
            existing['affected_trace_count'] = len(existing['all_affected_traces'])
            break

    return unique_schemas

  def _prioritize_schemas(
    self, schemas: List[Dict[str, Any]], issues: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """Sort schemas by priority."""
    # Sort by priority score (descending)
    schemas.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

    # Limit to top 15 schemas
    return schemas[:15]

  def _create_baseline_schemas(self, agent_understanding: str) -> List[Dict[str, Any]]:
    """Create baseline subjective quality schemas as fallback."""
    return [
      {
        'key': 'response_clarity',
        'name': 'Response Clarity',
        'label_type': 'FEEDBACK',
        'schema_type': 'categorical',
        'description': 'The response was clear and easy to understand',
        'rationale': 'Clear communication is essential for user understanding',
        'priority_score': 70,
        'grounded_in_traces': [],
        'all_affected_traces': [],
        'affected_trace_count': 0,
      },
      {
        'key': 'response_actionable',
        'name': 'Response Actionability',
        'label_type': 'FEEDBACK',
        'schema_type': 'categorical',
        'description': 'The response provided actionable information or next steps',
        'rationale': 'Users need actionable guidance to resolve their issues',
        'priority_score': 65,
        'grounded_in_traces': [],
        'all_affected_traces': [],
        'affected_trace_count': 0,
      },
      {
        'key': 'domain_expertise',
        'name': 'Domain Knowledge',
        'label_type': 'FEEDBACK',
        'schema_type': 'categorical',
        'description': 'The agent demonstrated appropriate domain knowledge',
        'rationale': 'Domain expertise affects the quality and accuracy of responses',
        'priority_score': 60,
        'grounded_in_traces': [],
        'all_affected_traces': [],
        'affected_trace_count': 0,
      },
      {
        'key': 'additional_observations',
        'name': 'Additional Observations',
        'label_type': 'FEEDBACK',
        'schema_type': 'text',
        'description': 'Any quality issues or notable behaviors not covered above',
        'max_length': 500,
        'rationale': 'Capture subjective issues requiring domain expertise',
        'priority_score': 0,
        'grounded_in_traces': [],
        'all_affected_traces': [],
        'affected_trace_count': 0,
      },
    ]
