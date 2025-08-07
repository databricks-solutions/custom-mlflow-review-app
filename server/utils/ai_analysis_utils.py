"""AI-Powered Experiment Analysis Utilities

This module provides AI-driven analysis of MLflow experiments using model serving endpoints
to generate dynamic, contextual reports about agent performance and patterns.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from dotenv import load_dotenv

from .config import config
from .experiment_analysis import ExperimentAnalyzer
from .labeling_items_utils import labeling_items_utils
from .labeling_sessions_utils import get_labeling_session
from .mlflow_utils import get_trace
from .model_serving_utils import ModelServingClient
from .review_apps_utils import review_apps_utils
from .trace_analysis import analyze_trace_patterns

# Load environment variables
load_dotenv('.env.local')

logger = logging.getLogger(__name__)


class AIExperimentAnalyzer:
  """AI-powered analyzer for MLflow experiments and labeling sessions."""

  def __init__(self, model_endpoint: str = None):
    """Initialize the AI analyzer with model serving client.

    Args:
        model_endpoint: Name of the model serving endpoint to use (defaults to config)
    """
    self.model_client = ModelServingClient()
    self.model_endpoint = model_endpoint or config.model_endpoint
    logger.info(f'Initialized AI analyzer with endpoint: {self.model_endpoint}')

  async def analyze_experiment(
    self, experiment_id: str, analysis_focus: str = 'comprehensive', trace_sample_size: int = 50
  ) -> Dict[str, Any]:
    """Generate comprehensive analysis using open-ended discovery.

    Args:
        experiment_id: MLflow experiment ID to analyze
        analysis_focus: Focus area - "comprehensive", "sme-engagement", "issue-analysis"
        trace_sample_size: Number of traces to analyze in detail

    Returns:
        Dictionary with comprehensive analysis, issues, and schemas
    """
    try:
      logger.info(f'Starting open-ended analysis of experiment {experiment_id}')
      
      # Use the new modular analyzer
      analyzer = ExperimentAnalyzer(model_endpoint=self.model_endpoint)
      result = await analyzer.analyze_experiment(
        experiment_id=experiment_id,
        focus=analysis_focus,
        trace_sample_size=trace_sample_size
      )
      
      logger.info('Open-ended experiment analysis completed successfully')
      return result

    except Exception as e:
      logger.error(f'Error in experiment analysis: {e}')
      return {'status': 'error', 'error': str(e), 'experiment_id': experiment_id}

  async def analyze_labeling_session(
    self, review_app_id: str, session_id: str, analysis_type: str = 'sme_insights'
  ) -> Dict[str, Any]:
    """Generate AI-powered analysis of labeling session results.

    Args:
        review_app_id: Review app ID
        session_id: Labeling session ID
        analysis_type: Type of analysis - "sme_insights", "quality_patterns", "completion_analysis"

    Returns:
        Dictionary with AI-generated labeling analysis
    """
    try:
      logger.info(f'Starting AI analysis of labeling session {session_id}')

      # Gather session data
      session_data = await self._gather_session_data(review_app_id, session_id)

      # Build analysis prompt
      session_prompt = self._build_session_analysis_prompt(session_data, analysis_type)

      # Get AI insights
      ai_response = await self._call_ai_model(session_prompt)

      # Structure the response
      structured_analysis = self._structure_session_response(
        ai_response, session_data, analysis_type
      )

      logger.info('AI labeling session analysis completed successfully')
      return structured_analysis

    except Exception as e:
      logger.error(f'Error in AI session analysis: {e}')
      return {'status': 'error', 'error': str(e), 'session_id': session_id}

  async def _perform_sme_analysis(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive SME-focused analysis using all four utilities.

    IMPORTANT: This method provides ANALYSIS and RECOMMENDATIONS only - it does not create
    any actual labeling sessions or schemas.

    Returns:
        Dictionary with comprehensive SME analysis including issue detection, schema
        recommendations, session curation suggestions, and impact analysis
    """
    try:
      logger.info('Starting comprehensive SME analysis with all four utilities')

      # Convert raw traces from experiment_data for analysis
      raw_sample_traces = []
      trace_analysis = experiment_data.get('trace_analysis', {})

      # Get actual trace objects for detailed analysis
      from .mlflow_utils import search_traces

      experiment_id = (
        experiment_data.get('experiment_info', {}).get('experiment', {}).get('experiment_id')
      )

      if experiment_id:
        raw_traces = search_traces(
          experiment_ids=[experiment_id],
          max_results=experiment_data.get('sample_size', 50),
          order_by=['timestamp_ms DESC'],
        )

        # Convert to analysis format
        for trace in raw_traces:
          try:
            trace_dict = {
              'info': {
                'trace_id': trace.info.trace_id,
                'experiment_id': trace.info.experiment_id,
                'execution_time_ms': trace.info.execution_time_ms,
                'status': trace.info.status,
                'timestamp_ms': trace.info.timestamp_ms,
              },
              'data': {'spans': []},
            }

            # Add span data if available
            if trace.data and trace.data.spans:
              for span in trace.data.spans:
                span_dict = {
                  'name': getattr(span, 'name', 'unknown'),
                  'span_type': getattr(span, 'span_type', 'UNKNOWN'),
                  'start_time_ms': getattr(span, 'start_time_ms', 0),
                  'end_time_ms': getattr(span, 'end_time_ms', 0),
                  'inputs': getattr(span, 'inputs', {}),
                  'outputs': getattr(span, 'outputs', {}),
                }
                trace_dict['data']['spans'].append(span_dict)

            raw_sample_traces.append(trace_dict)
          except Exception as e:
            logger.warning(f'Error converting trace for SME analysis: {e}')
            continue

      # 1. Issue Detection - identify critical problems that need SME attention
      issue_detector = SMEIssueDetector()
      issue_analysis = issue_detector.detect_critical_issues(raw_sample_traces)
      detected_issues = issue_analysis.get('issues', [])

      logger.info(f'Detected {len(detected_issues)} critical issues requiring SME attention')

      # 2. Schema Recommendations - suggest labeling schemas based on detected issues
      schema_recommender = SMESchemaRecommender()
      schema_recommendations = schema_recommender.recommend_schemas(detected_issues)

      logger.info(f'Generated {len(schema_recommendations)} schema recommendations')

      # 3. Session Curation - suggest targeted labeling session configurations
      session_curator = SMESessionCurator()
      session_suggestions = session_curator.create_curated_sessions(
        raw_sample_traces, detected_issues, schema_recommendations
      )

      logger.info(f'Created {len(session_suggestions)} session curation suggestions')

      logger.info('Completed comprehensive SME analysis')

      return {
        'issue_detection': {
          'summary': issue_analysis.get('summary', {}),
          'detected_issues': detected_issues,
          'raw_statistics': issue_analysis.get('raw_data', {}),
        },
        'schema_recommendations': {
          'recommended_schemas': schema_recommendations,
          'creation_guidance': 'These are RECOMMENDATIONS for schemas to create - not actual schemas',
        },
        'session_curation': {
          'session_suggestions': session_suggestions,
          'curation_guidance': 'These are SUGGESTIONS for labeling sessions to create - not actual sessions',
        },
        'comprehensive_summary': {
          'total_traces_analyzed': len(raw_sample_traces),
          'critical_issues_found': len(
            [i for i in detected_issues if i.get('severity') == 'critical']
          ),
          'high_priority_issues': len([i for i in detected_issues if i.get('severity') == 'high']),
          'recommended_schemas_count': len(schema_recommendations),
          'suggested_sessions_count': len(session_suggestions),
        },
      }

    except Exception as e:
      logger.error(f'Error in comprehensive SME analysis: {e}')
      return {
        'error': f'Failed to perform SME analysis: {str(e)}',
        'issue_detection': {'detected_issues': []},
        'schema_recommendations': {'recommended_schemas': []},
        'session_curation': {'session_suggestions': []},
      }

  async def _gather_experiment_data(self, experiment_id: str, sample_size: int) -> Dict[str, Any]:
    """Gather comprehensive experiment data for AI analysis."""
    try:
      # Get experiment info
      from .mlflow_utils import get_experiment

      experiment_info = get_experiment(experiment_id)

      # Get trace patterns
      trace_analysis = analyze_trace_patterns(experiment_id=experiment_id, limit=sample_size)

      # Get sample traces with detailed content
      from .mlflow_utils import search_traces

      raw_sample_traces = search_traces(
        experiment_ids=[experiment_id],
        max_results=min(5, sample_size),
        order_by=['timestamp_ms DESC'],
      )

      # Convert trace objects to serializable format
      sample_traces = []
      for trace in raw_sample_traces[:3]:  # Limit to first 3 for context
        try:
          trace_dict = {
            'trace_id': trace.info.trace_id,
            'experiment_id': trace.info.experiment_id,
            'timestamp_ms': trace.info.timestamp_ms,
            'execution_time_ms': trace.info.execution_time_ms,
            'status': trace.info.status,
            'request_id': getattr(trace.info, 'request_id', None),
            'data': {
              'request': getattr(trace.data, 'request', 'No request data'),
              'response': getattr(trace.data, 'response', 'No response data'),
              'spans_count': len(trace.data.spans) if trace.data and trace.data.spans else 0,
            },
          }
          sample_traces.append(trace_dict)
        except Exception as e:
          logger.warning(f'Error converting trace {trace.info.trace_id}: {e}')
          continue

      return {
        'experiment_info': experiment_info,
        'trace_analysis': trace_analysis,
        'sample_traces': sample_traces,
        'sample_size': sample_size,
        'total_traces': len(raw_sample_traces) if raw_sample_traces else 0,
      }

    except Exception as e:
      logger.error(f'Error gathering experiment data: {e}')
      raise

  async def _gather_session_data(self, review_app_id: str, session_id: str) -> Dict[str, Any]:
    """Gather comprehensive session data for AI analysis."""
    try:
      # Get session details
      session = await get_labeling_session(review_app_id, session_id)

      # Get review app for schema context
      review_app = await review_apps_utils.get_review_app(review_app_id)

      # Get labeling items and results
      items_response = await labeling_items_utils.list_items(
        review_app_id=review_app_id, labeling_session_id=session_id
      )

      items = items_response.get('items', [])
      completed_items = [item for item in items if item.get('state') == 'COMPLETED']

      # Get sample traces that were labeled
      sample_trace_ids = []
      for item in completed_items[:5]:  # Sample of completed items
        source = item.get('source', {})
        if source.get('trace_id'):
          sample_trace_ids.append(source['trace_id'])

      sample_traces = []
      for trace_id in sample_trace_ids:
        try:
          raw_trace = get_trace(trace_id)
          # Convert to expected format
          trace_data = {
            'info': {
              'trace_id': raw_trace.info.trace_id,
              'experiment_id': raw_trace.info.experiment_id,
              'assessments': [],
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

          sample_traces.append(trace_data)
        except:
          continue

      return {
        'session': session,
        'review_app': review_app,
        'items': items,
        'completed_items': completed_items,
        'sample_traces': sample_traces,
        'completion_rate': len(completed_items) / len(items) * 100 if items else 0,
        'schemas': review_app.get('labeling_schemas', []),
      }

    except Exception as e:
      logger.error(f'Error gathering session data: {e}')
      raise

  def _build_analysis_prompt(
    self, experiment_data: Dict[str, Any], focus: str
  ) -> List[Dict[str, str]]:
    """Build the analysis prompt for the AI model."""
    experiment_info = experiment_data.get('experiment_info', {})
    trace_analysis = experiment_data.get('trace_analysis', {})
    sample_traces = experiment_data.get('sample_traces', {})

    system_prompt = f"""You are an expert AI system analyst specializing in MLflow experiments and agent performance evaluation. 
        
Your task is to analyze experiment data and provide comprehensive insights about agent behavior, patterns, and recommendations.

Focus Area: {focus}

Analysis Guidelines:
- Be specific and data-driven in your analysis
- Identify concrete patterns and trends
- Provide actionable recommendations
- Use technical terminology appropriately
- Structure your response clearly with sections and bullet points
- Focus on practical insights for improving agent performance"""

    user_prompt = f"""Please analyze this MLflow experiment data:

**EXPERIMENT OVERVIEW:**
- Name: {experiment_info.get('name', 'Unknown')}
- ID: {experiment_info.get('experiment_id', 'Unknown')}
- Total Traces: {experiment_data.get('total_traces', 0)}

**TRACE ANALYSIS SUMMARY:**
{json.dumps(trace_analysis, indent=2)}

**SAMPLE TRACES (First 5):**
{json.dumps(sample_traces, indent=2, default=str)[:8000]}  # Truncate for context limits

Please provide a comprehensive analysis covering:

1. **Agent Architecture & Capabilities**: What type of agent this is and what it can do
2. **Performance Patterns**: Key patterns in execution, success rates, and efficiency
3. **Tool Usage Analysis**: How the agent uses available tools and workflows
4. **Quality Indicators**: Signs of high/low quality responses based on trace content
5. **Recommendations**: Specific suggestions for improvement or evaluation focus
6. **Evaluation Schema Suggestions**: What labeling schemas would be most effective for evaluating this agent

Format your response as structured markdown with clear sections."""

    return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]

  def _build_comprehensive_analysis_prompt(
    self, experiment_data: Dict[str, Any], sme_analysis: Dict[str, Any], focus: str
  ) -> List[Dict[str, str]]:
    """Build comprehensive analysis prompt incorporating SME analysis results."""
    experiment_info = experiment_data.get('experiment_info', {})
    trace_analysis = experiment_data.get('trace_analysis', {})

    # Extract key SME analysis components
    detected_issues = sme_analysis.get('issue_detection', {}).get('detected_issues', [])
    schema_recommendations = sme_analysis.get('schema_recommendations', {}).get(
      'recommended_schemas', []
    )
    session_suggestions = sme_analysis.get('session_curation', {}).get('session_suggestions', [])
    comprehensive_summary = sme_analysis.get('comprehensive_summary', {})

    system_prompt = f"""You are an expert MLflow experiment analyst specializing in detecting quality issues in AI agent responses.

Your task is to:
1. Identify the agent/model type from trace patterns
2. Detect QUALITY ISSUES in agent responses:
   - Wrong tool selection or misuse
   - Unfaithful responses (not matching tool outputs)
   - Tone/professionalism problems
   - Correctness issues and hallucinations
   - Style inconsistencies or weird phrasing
   - Logic errors or contradictions
3. Provide SPECIFIC TRACE EXAMPLES showing each issue
4. Ground evaluation schemas in REAL problems found

Focus Area: {focus}

Analysis Guidelines:
- ALWAYS cite specific trace IDs and quote problematic text
- Focus on quality, correctness, and professionalism
- Link each schema recommendation to actual issues found
- Show trace snippets demonstrating problems
- NO cost estimates, SME hours, or implementation topics"""

    user_prompt = f"""Please provide a comprehensive SME engagement analysis for this MLflow experiment:

**EXPERIMENT OVERVIEW:**
- Name: {experiment_info.get('experiment', {}).get('name', 'Unknown')}
- ID: {experiment_info.get('experiment', {}).get('experiment_id', 'Unknown')} 
- Total Traces Analyzed: {comprehensive_summary.get('total_traces_analyzed', 0)}

**CRITICAL ISSUES DETECTED ({len(detected_issues)} total):**
{json.dumps(detected_issues, indent=2)[:3000]}

**SCHEMA RECOMMENDATIONS ({len(schema_recommendations)} total):**
{json.dumps(schema_recommendations, indent=2)[:2000]}

**SESSION CURATION SUGGESTIONS ({len(session_suggestions)} total):**
{json.dumps(session_suggestions, indent=2)[:2000]}

**TRACE PATTERNS & STATISTICS:**
{json.dumps(trace_analysis, indent=2)[:2000]}

Please provide a quality-focused analysis:

## 🤖 Agent Identification
Briefly identify the agent type and its intended purpose.

## 🚨 Quality Issues Found
For EACH issue type:
1. **Issue Description**: What's wrong
2. **Example Traces**: 
   - Trace ID: [provide clickable trace_id]
   - Problem snippet: "quote the problematic text"
   - Why it's wrong: [explanation]
3. **Frequency**: How often this occurs

## 📋 Evaluation Schemas with Rationale
For EACH recommended schema:
1. **Schema Name**: [descriptive name]
2. **Type**: rating/category/text
3. **What to Evaluate**: [specific criteria]
4. **Grounded in These Issues**:
   - Link to trace examples above
   - Quote specific problems this schema would catch
5. **Expected Impact**: How this helps improve quality

## 🔍 Specific Quality Problems
Detail any issues with:
- **Correctness**: Factual errors, hallucinations
- **Faithfulness**: Not matching tool outputs
- **Professionalism**: Tone, style issues
- **Tool Usage**: Wrong tools, misuse
- **Logic**: Contradictions, nonsensical responses

ALWAYS include trace IDs and quoted examples. Make schemas directly address found issues."""

    return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]

  def _build_session_analysis_prompt(
    self, session_data: Dict[str, Any], analysis_type: str
  ) -> List[Dict[str, str]]:
    """Build the session analysis prompt for the AI model."""
    session = session_data.get('session', {})
    completed_items = session_data.get('completed_items', [])
    completion_rate = session_data.get('completion_rate', 0)
    schemas = session_data.get('schemas', [])

    system_prompt = f"""You are an expert SME evaluation analyst specializing in labeling session analysis and human feedback patterns.

Your task is to analyze labeling session results and provide insights about SME behavior, assessment quality, and evaluation effectiveness.

Analysis Type: {analysis_type}

Analysis Guidelines:
- Focus on SME behavior and feedback patterns
- Identify assessment quality indicators
- Look for consensus, disagreements, and outliers
- Provide insights about evaluation effectiveness
- Suggest improvements for future labeling sessions
- Be specific about statistical patterns and trends"""

    # Extract SME feedback patterns
    sme_responses = {}
    for item in completed_items:
      labels = item.get('labels', {})
      for schema_name, label_value in labels.items():
        if schema_name not in sme_responses:
          sme_responses[schema_name] = []
        sme_responses[schema_name].append(label_value)

    user_prompt = f"""Please analyze this labeling session data:

**SESSION OVERVIEW:**
- Session Name: {session.get('name', 'Unknown')}
- Completion Rate: {completion_rate:.1f}%
- Total Items: {len(session_data.get('items', []))}
- Completed Items: {len(completed_items)}

**LABELING SCHEMAS:**
{json.dumps(schemas, indent=2)[:2000]}

**SME RESPONSES SUMMARY:**
{json.dumps(sme_responses, indent=2, default=str)[:4000]}

**SAMPLE COMPLETED ITEMS:**
{json.dumps(completed_items[:3], indent=2, default=str)[:4000]}

Please provide a detailed analysis covering:

1. **SME Engagement Analysis**: Completion patterns, dropout points, engagement quality
2. **Assessment Quality Patterns**: Consistency, variance, and reliability of SME judgments
3. **Schema Effectiveness**: Which schemas produce the most useful feedback
4. **Consensus & Disagreement Areas**: Where SMEs agree/disagree and why
5. **Content-Assessment Correlations**: What trace characteristics lead to different ratings
6. **Improvement Recommendations**: How to increase completion rates and assessment quality
7. **Next Steps**: Specific actions to optimize the labeling process

Format your response as structured markdown with actionable insights."""

    return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]

  async def _call_ai_model(self, messages: List[Dict[str, str]]) -> str:
    """Call the AI model with the analysis prompt."""
    try:
      response = self.model_client.query_endpoint(
        endpoint_name=self.model_endpoint,
        messages=messages,
        temperature=0.3,  # Lower temperature for more consistent analysis
        max_tokens=2000,  # Longer responses for detailed analysis
        stream=False,
      )

      # Extract response content
      if isinstance(response, dict):
        choices = response.get('choices', [])
        if choices and len(choices) > 0:
          message = choices[0].get('message', {})
          return message.get('content', str(response))

      return str(response)

    except Exception as e:
      logger.error(f'Error calling AI model: {e}')
      raise

  def _structure_ai_response(
    self, ai_response: str, experiment_data: Dict[str, Any], focus: str
  ) -> Dict[str, Any]:
    """Structure the AI response into a comprehensive analysis result."""
    return {
      'status': 'success',
      'analysis_type': 'experiment_analysis',
      'focus': focus,
      'experiment_id': experiment_data.get('experiment_info', {}).get('experiment_id'),
      'ai_analysis': ai_response,
      'metadata': {
        'total_traces_analyzed': experiment_data.get('total_traces', 0),
        'sample_size': experiment_data.get('sample_size', 0),
        'model_endpoint': self.model_endpoint,
        'analysis_timestamp': asyncio.get_event_loop().time(),
      },
      'raw_data': {
        'experiment_info': experiment_data.get('experiment_info'),
        'trace_patterns': experiment_data.get('trace_analysis'),
      },
    }

  def _structure_comprehensive_response(
    self,
    ai_response: str,
    experiment_data: Dict[str, Any],
    sme_analysis: Dict[str, Any],
    focus: str,
  ) -> Dict[str, Any]:
    """Structure the comprehensive SME-focused AI response."""
    comprehensive_summary = sme_analysis.get('comprehensive_summary', {})
    detected_issues = sme_analysis.get('issue_detection', {}).get('detected_issues', [])
    schema_recommendations = sme_analysis.get('schema_recommendations', {}).get(
      'recommended_schemas', []
    )
    session_suggestions = sme_analysis.get('session_curation', {}).get('session_suggestions', [])

    return {
      'status': 'success',
      'analysis_type': 'comprehensive_sme_engagement',
      'focus': focus,
      'experiment_id': experiment_data.get('experiment_info', {})
      .get('experiment', {})
      .get('experiment_id'),
      'ai_analysis': ai_response,
      'executive_summary': {
        'total_traces_analyzed': comprehensive_summary.get('total_traces_analyzed', 0),
        'critical_issues_found': comprehensive_summary.get('critical_issues_found', 0),
        'high_priority_issues': comprehensive_summary.get('high_priority_issues', 0),
        'recommended_schemas': comprehensive_summary.get('recommended_schemas_count', 0),
        'suggested_sessions': comprehensive_summary.get('suggested_sessions_count', 0),
      },
      'sme_engagement_plan': {
        'critical_issues': [
          {
            'issue_type': issue.get('issue_type'),
            'severity': issue.get('severity'),
            'title': issue.get('title'),
            'affected_traces': issue.get('affected_traces', 0),
            'sme_focus': issue.get('sme_focus', {}),
          }
          for issue in detected_issues[:5]  # Top 5 most critical
        ],
        'recommended_schemas': [
          {
            'schema_name': schema.get('name'),
            'schema_type': schema.get('schema_type'),
            'priority_score': schema.get('priority_score', 0),
            'target_issue_type': schema.get('target_issue_type'),
            'description': schema.get('description'),
          }
          for schema in schema_recommendations
        ],
        'session_configurations': [
          {
            'session_name': session.get('session_name'),
            'session_type': session.get('session_type'),
            'target_issue': session.get('target_issue'),
            'trace_count': session.get('trace_count', 0),
            'priority': session.get('priority'),
            'estimated_completion_time': session.get('estimated_completion_time'),
          }
          for session in session_suggestions
        ],
      },
      'implementation_guidance': {
        'disclaimer': 'These are ANALYSIS and RECOMMENDATIONS only - not actual resource creation',
        'next_steps': [
          'Review recommended schemas and create the most impactful ones',
          'Set up suggested labeling sessions focusing on critical issues',
          'Engage SMEs with clear guidance on focus areas',
          'Monitor completion rates and assessment quality',
          'Iterate based on SME feedback and results',
        ],
        'creation_commands': {
          'schemas': 'Use /label-schemas add commands or tools/create_labeling_schemas.py',
          'sessions': 'Use /labeling-sessions add commands or tools/create_labeling_session.py',
        },
      },
      'metadata': {
        'total_traces_analyzed': comprehensive_summary.get('total_traces_analyzed', 0),
        'sample_size': experiment_data.get('sample_size', 0),
        'model_endpoint': self.model_endpoint,
        'analysis_timestamp': asyncio.get_event_loop().time(),
      },
      'raw_sme_analysis': sme_analysis,
      'raw_experiment_data': {
        'experiment_info': experiment_data.get('experiment_info'),
        'trace_patterns': experiment_data.get('trace_analysis'),
      },
    }

  def _structure_session_response(
    self, ai_response: str, session_data: Dict[str, Any], analysis_type: str
  ) -> Dict[str, Any]:
    """Structure the AI session analysis response."""
    return {
      'status': 'success',
      'analysis_type': 'session_analysis',
      'session_analysis_type': analysis_type,
      'session_id': session_data.get('session', {}).get('labeling_session_id'),
      'ai_analysis': ai_response,
      'metadata': {
        'completion_rate': session_data.get('completion_rate', 0),
        'total_items': len(session_data.get('items', [])),
        'completed_items': len(session_data.get('completed_items', [])),
        'schemas_count': len(session_data.get('schemas', [])),
        'model_endpoint': self.model_endpoint,
        'analysis_timestamp': asyncio.get_event_loop().time(),
      },
      'raw_data': {
        'session': session_data.get('session'),
        'completion_stats': {
          'total': len(session_data.get('items', [])),
          'completed': len(session_data.get('completed_items', [])),
          'completion_rate': session_data.get('completion_rate', 0),
        },
      },
    }


# Utility functions for common analysis tasks
async def analyze_experiment_with_comprehensive_sme_insights(
  experiment_id: str,
  focus: str = 'comprehensive',
  model_endpoint: str = None,
  trace_sample_size: int = 50,
) -> Dict[str, Any]:
  """Generate comprehensive SME engagement analysis for an MLflow experiment.

  IMPORTANT: This function provides ANALYSIS and RECOMMENDATIONS only - it does not
  create any actual labeling sessions or schemas.

  Args:
      experiment_id: MLflow experiment ID
      focus: Analysis focus area - "comprehensive", "sme-engagement", "issue-analysis"
      model_endpoint: Model serving endpoint to use
      trace_sample_size: Number of traces to analyze for comprehensive insights

  Returns:
      Comprehensive SME engagement analysis with issue detection, schema recommendations,
      session curation suggestions, and impact analysis
  """
  analyzer = AIExperimentAnalyzer(model_endpoint)
  return await analyzer.analyze_experiment(experiment_id, focus, trace_sample_size)


async def analyze_experiment_with_ai(
  experiment_id: str,
  focus: str = 'comprehensive',
  model_endpoint: str = None,
) -> Dict[str, Any]:
  """Legacy convenience function - use analyze_experiment_with_comprehensive_sme_insights instead."""
  return await analyze_experiment_with_comprehensive_sme_insights(
    experiment_id, focus, model_endpoint
  )


async def analyze_session_with_ai(
  review_app_id: str,
  session_id: str,
  analysis_type: str = 'sme_insights',
  model_endpoint: str = None,
) -> Dict[str, Any]:
  """Convenience function to analyze a labeling session with AI.

  Args:
      review_app_id: Review app ID
      session_id: Labeling session ID
      analysis_type: Type of analysis to perform
      model_endpoint: Model serving endpoint to use

  Returns:
      AI session analysis results
  """
  analyzer = AIExperimentAnalyzer(model_endpoint)
  return await analyzer.analyze_labeling_session(review_app_id, session_id, analysis_type)
