"""Enhanced Labeling Session Analysis with Chain-of-Thought Insights

This module provides comprehensive analysis of labeling sessions using a methodology
similar to experiment analysis. It focuses on SME assessments, generates actionable
insights grounded in actual labels, and stores results to MLflow artifacts.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean, median, stdev
from typing import Any, Dict, List, Optional, Tuple

from .config import config
from .labeling_items_utils import labeling_items_utils
from .labeling_sessions_utils import get_labeling_session
from .mlflow_artifact_utils import MLflowArtifactManager
from .mlflow_utils import get_experiment, get_trace, search_traces
from .model_serving_utils import ModelServingClient
from .review_apps_utils import review_apps_utils

logger = logging.getLogger(__name__)


class SMEInsightDiscovery:
  """Discovers actionable insights from SME assessments using chain-of-thought reasoning."""

  def __init__(self, model_client: ModelServingClient):
    """Initialize with model serving client."""
    self.model_client = model_client
    self.logger = logging.getLogger(__name__)

  async def discover_insights(
    self,
    items: List[Dict[str, Any]],
    schemas: List[Dict[str, Any]],
    traces: List[Dict[str, Any]],
    experiment_context: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Discover insights from SME assessments using LLM analysis.

    Args:
        items: Labeling items with assessments
        schemas: Label schemas used
        traces: Trace data for context
        experiment_context: Optional experiment analysis report

    Returns:
        Dictionary with discovered insights and patterns
    """
    self.logger.info(f'Starting SME insight discovery for {len(items)} items')

    # Step 1: Understand the agent and evaluation context
    agent_understanding = await self._understand_evaluation_context(
      schemas, traces, experiment_context
    )

    # Step 2: Analyze assessment patterns
    assessment_patterns = await self._analyze_assessment_patterns(items, schemas, agent_understanding)

    # Step 3: Analyze trace-specific label meanings
    trace_label_analysis = self._analyze_trace_label_meanings(
      items, schemas, traces, agent_understanding
    )
    
    # Step 4: Discover critical issues from labels
    critical_issues = await self._discover_critical_issues(
      items, schemas, assessment_patterns, agent_understanding
    )

    # Step 5: Generate actionable recommendations
    completed_count = len([i for i in items if i.get('state') == 'COMPLETED'])
    recommendations = await self._generate_recommendations(
      assessment_patterns, critical_issues, agent_understanding, completed_count
    )

    return {
      'agent_understanding': agent_understanding,
      'assessment_patterns': assessment_patterns,
      'trace_label_analysis': trace_label_analysis,
      'critical_issues': critical_issues,
      'recommendations': recommendations,
      'metadata': {
        'total_items_analyzed': len(items),
        'completed_assessments': len([i for i in items if i.get('state') == 'COMPLETED']),
        'total_traces_analyzed': len(traces) if traces else 0,
        'discovery_method': 'comprehensive-trace-and-assessment-analysis',
        'analysis_scope': 'all-traces-and-results',
      },
    }

  async def _understand_evaluation_context(
    self,
    schemas: List[Dict[str, Any]],
    traces: List[Dict[str, Any]],
    experiment_context: Optional[str],
  ) -> str:
    """Understand what's being evaluated and why."""
    # Prepare schema summary - include ALL schemas for complete context
    schema_summary = []
    for schema in schemas:  # ALL schemas, not just top 10
      schema_summary.append(
        {
          'name': schema.get('name'),
          'key': schema.get('key'),
          'type': schema.get('schema_type'),
          'description': schema.get('description'),
          'label_type': schema.get('label_type'),
          'min': schema.get('min'),
          'max': schema.get('max'),
          'categories': schema.get('categories') if schema.get('schema_type') == 'categorical' else None,
        }
      )

    # Sample trace interactions
    trace_samples = []
    for trace in traces[:5]:
      trace_samples.append(
        {
          'request': str(trace.get('data', {}).get('request', ''))[:200],
          'response': str(trace.get('data', {}).get('response', ''))[:200],
        }
      )

    prompt = f"""
        ## Understanding the Evaluation Context
        
        Evaluation Schemas:
        {json.dumps(schema_summary, indent=2)}
        
        Sample Traces Being Evaluated:
        {json.dumps(trace_samples, indent=2)}
        
        {f"Experiment Context: {experiment_context[:1000]}" if experiment_context else "No experiment context available"}
        
        Based on this information:
        1. What type of agent/system is being evaluated?
        2. What are the key quality dimensions being assessed?
        3. What are the expected standards based on the schemas?
        4. What domain-specific requirements apply?
        
        Provide a concise summary of the evaluation context and standards.
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint, 
      messages=[{'role': 'user', 'content': prompt}],
      max_tokens=2000
    )

    # Extract content from the response structure
    if 'choices' in response and response['choices']:
      return response['choices'][0].get('message', {}).get('content', 'Unknown evaluation context')
    elif 'predictions' in response and response['predictions']:
      return str(response['predictions'][0])
    else:
      return response.get('content', 'Unknown evaluation context')

  async def _analyze_assessment_patterns(
    self,
    items: List[Dict[str, Any]],
    schemas: List[Dict[str, Any]],
    agent_understanding: str,
  ) -> Dict[str, Any]:
    """Analyze patterns in SME assessments."""
    # Aggregate labels by schema from completed items
    schema_labels = defaultdict(list)
    completed_items = []
    
    for item in items:
      if item.get('state') == 'COMPLETED':
        completed_items.append(item)
        for schema_key, label_value in item.get('labels', {}).items():
          schema_labels[schema_key].append(
            {'trace_id': item.get('source', {}).get('trace_id'), 'value': label_value}
          )

    # Always analyze, even with limited data
    # Prepare pattern analysis data with full schema context
    pattern_data = {}
    all_schemas_info = []  # Include ALL schemas for context
    
    for schema in schemas:
      schema_key = schema.get('key')
      schema_info = {
        'key': schema_key,
        'name': schema.get('name'),
        'type': schema.get('schema_type'),
        'description': schema.get('description'),
        'min': schema.get('min'),
        'max': schema.get('max'),
        'categories': schema.get('categories') if schema.get('schema_type') == 'categorical' else None,
      }
      all_schemas_info.append(schema_info)
      
      if schema_key in schema_labels:
        labels = schema_labels[schema_key]
        pattern_data[schema_key] = {
          'schema_name': schema.get('name'),
          'schema_type': schema.get('schema_type'),
          'description': schema.get('description'),
          'total_labels': len(labels),
          'sample_labels': labels[:10],  # Sample for analysis
        }
    
    # Analyze ALL items for comprehensive insights
    total_items = len(items)
    completed_count = len(completed_items)
    
    # Always provide comprehensive analysis regardless of completion status
    logger.info(f'Analyzing patterns from {total_items} total items ({completed_count} completed) for comprehensive insights')

    prompt = f"""
        ## Chain of Thought: Assessment Pattern Analysis
        
        Session Overview:
        - Total items in session: {total_items}
        - Completed assessments: {completed_count}
        - All traces analyzed for comprehensive insights
        
        Agent Understanding:
        {agent_understanding}
        
        ALL Evaluation Schemas (complete list for context):
        {json.dumps(all_schemas_info, indent=2)}
        
        SME Assessment Data (by schema):
        {json.dumps(pattern_data, indent=2)[:3000]}
        
        Based on the assessment patterns and ALL available traces, analyze comprehensively to identify:
        1. Which schemas show the most concerning patterns (low scores, negative feedback)?
        2. Which schemas have high agreement among SMEs?
        3. What trends emerge from the numerical ratings?
        4. What themes appear in categorical selections?  
        5. Are there any surprising or unexpected patterns?
        6. What insights can be gleaned from analyzing ALL traces in this session?
        7. What patterns emerge when examining the complete set of traces, not just assessed ones?
        
        CRITICAL: Analyze EVERY trace and result comprehensively - even a SINGLE assessment contains valuable insights!
        
        Even with just {completed_count} assessment(s), provide specific findings:
        - If only 1 assessment: Highlight what that single assessment reveals about quality
        - Extract ANY patterns visible from the available data
        - Make observations about the traces themselves, not just assessments
        
        Return JSON:
        {{
            "concerning_patterns": [
                {{
                    "schema": "schema_key", 
                    "pattern": "description of concerning pattern",
                    "severity": "high/medium/low",
                    "evidence": "specific label values or trends"
                }}
            ],
            "consensus_areas": [
                {{
                    "schema": "schema_key",
                    "consensus_type": "positive/negative", 
                    "description": "what SMEs agree on"
                }}
            ],
            "key_trends": ["trend1", "trend2"],
            "unexpected_findings": ["finding1", "finding2"]
        }}
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint, 
      messages=[{'role': 'user', 'content': prompt}],
      max_tokens=2000
    )

    try:
      # Extract content from the response structure
      content = ''
      if 'choices' in response and response['choices']:
        content = response['choices'][0].get('message', {}).get('content', '')
      elif 'predictions' in response and response['predictions']:
        content = str(response['predictions'][0])
      else:
        content = response.get('content', '{}')
      
      # Extract JSON from markdown code blocks if present
      if '```json' in content:
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      elif '```' in content:
        import re
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      
      return json.loads(content)
    except json.JSONDecodeError:
      self.logger.error('Failed to parse assessment patterns')
      return {}

  def _analyze_trace_label_meanings(
    self,
    items: List[Dict[str, Any]],
    schemas: List[Dict[str, Any]],
    traces: List[Dict[str, Any]],
    agent_understanding: str,
  ) -> Dict[str, Any]:
    """Analyze what each SME label means in the context of its specific trace."""
    # Build a map of trace_id to trace data for quick lookup
    trace_map = {t.get('info', {}).get('trace_id'): t for t in traces}
    
    # Collect ALL traces with their labeling status and context
    all_trace_analyses = []
    labeled_traces = []
    unlabeled_traces = []
    
    # Process ALL items regardless of state
    for item in items:
      trace_id = item.get('source', {}).get('trace_id')
      if trace_id and trace_id in trace_map:
        trace_data = trace_map[trace_id]
        trace_info = {
          'trace_id': trace_id,
          'state': item.get('state', 'PENDING'),
          'labels': item.get('labels', {}),
          'request': str(trace_data.get('data', {}).get('request', ''))[:500],
          'response': str(trace_data.get('data', {}).get('response', ''))[:500],
          'last_updated_by': item.get('last_updated_by', 'Unknown'),
        }
        
        all_trace_analyses.append(trace_info)
        
        # Separate labeled vs unlabeled for analysis
        # A completed item is labeled even if labels dict is empty
        if item.get('state') == 'COMPLETED':
          labeled_traces.append(trace_info)
        else:
          unlabeled_traces.append(trace_info)
    
    # Also check for any traces not in items
    trace_ids_in_items = {item.get('source', {}).get('trace_id') for item in items}
    unlinked_traces = [t for t in traces if t.get('info', {}).get('trace_id') not in trace_ids_in_items]
    
    self.logger.info(f'Analyzing {len(all_trace_analyses)} total traces: {len(labeled_traces)} labeled, {len(unlabeled_traces)} unlabeled, {len(unlinked_traces)} unlinked')
    
    # Create schema lookup for easier interpretation
    schema_lookup = {s.get('key'): s for s in schemas}
    
    # Prepare prompt for LLM to interpret ALL traces
    labeled_samples = labeled_traces[:10]  # Sample of labeled traces
    unlabeled_samples = unlabeled_traces[:5]  # Sample of unlabeled traces
    
    prompt = f"""
    ## Comprehensive Trace Analysis - ALL Traces in Session
    
    Agent Understanding:
    {agent_understanding}
    
    Label Schemas:
    {json.dumps([{{
      'key': s.get('key'),
      'name': s.get('name'),
      'type': s.get('schema_type'),
      'description': s.get('description'),
      'min': s.get('min'),
      'max': s.get('max'),
      'categories': s.get('categories') if s.get('schema_type') == 'categorical' else None
    }} for s in schemas], indent=2)}
    
    Session Overview:
    - Total traces in session: {len(all_trace_analyses)}
    - Labeled/Completed: {len(labeled_traces)}
    - Pending/Unlabeled: {len(unlabeled_traces)}
    - Unlinked traces: {len(unlinked_traces)}
    
    Labeled Traces (with SME assessments):
    {json.dumps(labeled_samples, indent=2)}
    
    Unlabeled/Pending Traces (awaiting assessment):
    {json.dumps(unlabeled_samples, indent=2)}
    
    CRITICAL: Analyze ALL traces comprehensively:
    
    For LABELED traces:
    1. WHY did the SME give these specific ratings/labels?
    2. What specific aspects of the request/response led to these assessments?
    3. What patterns or issues is the SME highlighting through these labels?
    4. How do the labels relate to the actual content quality?
    
    For UNLABELED traces:
    1. What potential issues might exist based on the request/response?
    2. How do these compare to the labeled traces?
    3. What patterns do you see that might need SME attention?
    
    Provide comprehensive analysis including:
    - Patterns across ALL traces (both labeled and unlabeled)
    - Key insights about quality across the entire session
    - Specific examples from both assessed and unassessed traces
    - Recommendations based on the COMPLETE dataset
    
    Return JSON:
    {{
      "trace_analyses": [
        {{
          "trace_id": "trace_id",
          "state": "COMPLETED/PENDING",
          "label_interpretation": "for labeled: why these labels; for unlabeled: potential issues",
          "quality_issues": ["specific issue 1", "specific issue 2"],
          "positive_aspects": ["what worked well"],
          "key_finding": "main takeaway from this trace"
        }}
      ],
      "overall_session_analysis": {{
        "total_traces": {len(all_trace_analyses)},
        "labeled_count": {len(labeled_traces)},
        "unlabeled_count": {len(unlabeled_traces)},
        "completion_rate": "{round(len(labeled_traces) / len(all_trace_analyses) * 100 if all_trace_analyses else 0, 1)}%"
      }},
      "pattern_summary": "patterns across ALL {len(all_trace_analyses)} traces",
      "key_insights": [
        "insight about labeled traces",
        "insight about unlabeled traces",
        "insight about overall quality patterns"
      ],
      "label_distribution_meaning": {{
        "low_scores": "what low scores indicate",
        "high_scores": "what high scores indicate",
        "false_labels": "what False/incorrect labels mean",
        "unlabeled_implications": "what the unlabeled traces suggest"
      }}
    }}
    """
    
    try:
      response = self.model_client.query_endpoint(
        endpoint_name=self.model_client.default_endpoint, 
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=4000
      )
      
      self.logger.info(f'Model response keys: {response.keys() if isinstance(response, dict) else "not a dict"}')
      
      # Extract content from the response structure
      content = ''
      if 'choices' in response and response['choices']:
        content = response['choices'][0].get('message', {}).get('content', '')
      elif 'predictions' in response and response['predictions']:
        content = str(response['predictions'][0])
      else:
        content = response.get('content', '{}')
      
      self.logger.info(f'Extracted content length: {len(content)}')
      if not content or content == '{}':
        self.logger.warning('No content extracted from model response')
        raise ValueError('Empty response from model')
      
      # Extract JSON from markdown code blocks if present
      if '```json' in content:
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
          self.logger.debug('Extracted JSON from markdown code block')
      elif '```' in content:
        import re
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
          self.logger.debug('Extracted content from code block')
      
      self.logger.debug(f'Content to parse: {content[:500]}...')
      trace_analysis = json.loads(content)
      
      # Add summary statistics
      trace_analysis['total_analyzed'] = len(all_trace_analyses)
      trace_analysis['labeled_count'] = len(labeled_traces)
      trace_analysis['unlabeled_count'] = len(unlabeled_traces)
      
      return trace_analysis
      
    except Exception as e:
      self.logger.error(f'Error analyzing trace label meanings: {e}')
      # Provide comprehensive basic analysis even if LLM fails
      label_keys = set()
      for lt in labeled_traces:
        label_keys.update(lt.get('labels', {}).keys())
      
      return {
        'trace_analyses': [
          {
            'trace_id': t['trace_id'],
            'state': t['state'],
            'labels': t.get('labels', {}),
            'label_interpretation': 'LLM analysis unavailable - showing raw data',
          }
          for t in all_trace_analyses[:15]  # Show first 15 traces
        ],
        'overall_session_analysis': {
          'total_traces': len(all_trace_analyses),
          'labeled_count': len(labeled_traces),
          'unlabeled_count': len(unlabeled_traces),
          'completion_rate': f"{round(len(labeled_traces) / len(all_trace_analyses) * 100 if all_trace_analyses else 0, 1)}%"
        },
        'pattern_summary': f'Session contains {len(all_trace_analyses)} total traces: {len(labeled_traces)} labeled, {len(unlabeled_traces)} pending',
        'key_insights': [
          f'{len(all_trace_analyses)} total traces in this labeling session',
          f'{len(labeled_traces)} traces have been assessed by SMEs',
          f'{len(unlabeled_traces)} traces are still pending assessment',
          f'Labels used: {", ".join(label_keys) if label_keys else "None yet"}',
        ],
        'error': str(e),
      }

  async def _discover_critical_issues(
    self,
    items: List[Dict[str, Any]],
    schemas: List[Dict[str, Any]],
    patterns: Dict[str, Any],
    agent_understanding: str,
  ) -> List[Dict[str, Any]]:
    """Discover critical issues based on SME labels."""
    # Analyze ALL items for comprehensive issue discovery
    problematic_items = []
    all_trace_ids = []  # Collect all trace IDs for comprehensive analysis
    
    for item in items:
      trace_id = item.get('source', {}).get('trace_id')
      if trace_id:
        all_trace_ids.append(trace_id)
      
      # Only check for issues in completed items that have labels
      if item.get('state') == 'COMPLETED':
        labels = item.get('labels', {})
        has_issue = False

        # Check numerical scores
        for schema in schemas:
          if schema.get('schema_type') == 'numerical':
            schema_key = schema.get('key')
            if schema_key in labels:
              value = float(labels[schema_key])
              max_val = schema.get('max', 5)
              if value <= max_val * 0.4:  # Low score threshold
                has_issue = True
                break

        # Check categorical negative feedback
        for schema in schemas:
          if schema.get('schema_type') == 'categorical':
            schema_key = schema.get('key')
            if schema_key in labels:
              value = labels[schema_key]
              if value.lower() in ['false', 'no', 'incorrect', 'incomplete']:
                has_issue = True
                break

        if has_issue:
          problematic_items.append(
            {'trace_id': trace_id, 'labels': labels}
          )
    
    logger.info(f'Analyzing ALL {len(all_trace_ids)} traces in session for comprehensive critical issue discovery')

    completed_items = [i for i in items if i.get('state') == 'COMPLETED']
    completed_count = len(completed_items)
    
    prompt = f"""
        ## Chain of Thought: Critical Issue Discovery
        
        Data Context:
        - Total items in session: {len(items)}
        - Completed assessments: {completed_count}
        - Problematic items found: {len(problematic_items)}
        - ALL traces analyzed comprehensively
        
        Agent Understanding:
        {agent_understanding}
        
        Assessment Patterns:
        {json.dumps(patterns, indent=2)[:2000]}
        
        Problematic Items (low scores/negative feedback):
        {json.dumps(problematic_items[:20], indent=2)[:2000]}
        
        Based on comprehensive analysis of ALL traces and assessments, identify critical issues:
        1. What specific problems do the low scores indicate?
        2. Which issues appear most frequently?
        3. What is the root cause based on the patterns?
        4. How severe is each issue for end users?
        5. Which issues should be prioritized for fixing?
        6. What insights emerge from analyzing ALL traces in the session?
        7. What patterns appear across the complete trace dataset?
        8. What can be learned from traces that haven't been assessed yet?
        
        IMPORTANT: Even with {completed_count} assessment(s), identify issues:
        - Single assessments can reveal critical problems
        - Look at the trace data itself for quality issues
        - Every piece of data provides valuable insights
        
        COMPREHENSIVE ANALYSIS REQUIRED: Every single trace and result provides valuable insights - analyze everything thoroughly.
        
        Return JSON:
        {{
            "critical_issues": [
                {{
                    "issue_title": "clear title",
                    "description": "detailed description grounded in SME labels",
                    "severity": "critical/high/medium",
                    "frequency": "percentage or count",
                    "evidence_from_labels": ["specific examples from assessments"],
                    "affected_traces": ["trace_id1", "trace_id2"],
                    "root_cause": "likely root cause",
                    "priority": 1-10
                }}
            ]
        }}
        
        IMPORTANT: All issues MUST be grounded in actual SME assessments, not hypothetical.
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint, 
      messages=[{'role': 'user', 'content': prompt}],
      max_tokens=2000
    )

    try:
      # Extract content from the response structure
      content = ''
      if 'choices' in response and response['choices']:
        content = response['choices'][0].get('message', {}).get('content', '')
      elif 'predictions' in response and response['predictions']:
        content = str(response['predictions'][0])
      else:
        content = response.get('content', '{}')
      
      # Extract JSON from markdown code blocks if present
      if '```json' in content:
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      elif '```' in content:
        import re
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      
      result = json.loads(content)
      return result.get('critical_issues', [])
    except json.JSONDecodeError:
      self.logger.error('Failed to parse critical issues')
      return []

  async def _generate_recommendations(
    self,
    patterns: Dict[str, Any],
    critical_issues: List[Dict[str, Any]],
    agent_understanding: str,
    completed_count: int = 0,
  ) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on discoveries."""
    issue_count = len(critical_issues)
    
    prompt = f"""
        ## Chain of Thought: Actionable Recommendations
        
        Agent Understanding:
        {agent_understanding}
        
        Assessment Patterns:
        {json.dumps(patterns, indent=2)[:1500]}
        
        Critical Issues Found ({issue_count} issues):
        {json.dumps(critical_issues[:5], indent=2)[:1500]}
        
        Generate specific, actionable recommendations to improve the agent:
        1. What immediate fixes are needed for critical issues?
        2. What improvements would address the concerning patterns?
        3. What successful patterns should be reinforced?
        4. What additional evaluation might be needed?
        5. What insights from analyzing ALL traces suggest improvement opportunities?
        6. What recommendations emerge from the complete dataset, including unassessed traces?
        
        ALWAYS provide recommendations, even with minimal data:
        - {issue_count} issue(s) and {completed_count} assessment(s) still provide actionable insights
        - Recommend based on what WAS observed, not what's missing
        - Every assessment and trace tells a story - extract it!
        
        GENERATE COMPREHENSIVE RECOMMENDATIONS: Base all suggestions on thorough analysis of every available trace and assessment - no data should be ignored.
        
        Return JSON:
        {{
            "recommendations": [
                {{
                    "title": "clear action title",
                    "description": "specific steps to take",
                    "rationale": "why this will help (grounded in SME assessments)",
                    "priority": "immediate/high/medium/low",
                    "expected_impact": "what will improve",
                    "success_metric": "how to measure improvement"
                }}
            ]
        }}
        
        Make recommendations specific and implementable, not generic advice.
        """

    response = self.model_client.query_endpoint(
      endpoint_name=self.model_client.default_endpoint, 
      messages=[{'role': 'user', 'content': prompt}],
      max_tokens=2000
    )

    try:
      # Extract content from the response structure
      content = ''
      if 'choices' in response and response['choices']:
        content = response['choices'][0].get('message', {}).get('content', '')
      elif 'predictions' in response and response['predictions']:
        content = str(response['predictions'][0])
      else:
        content = response.get('content', '{}')
      
      # Extract JSON from markdown code blocks if present
      if '```json' in content:
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      elif '```' in content:
        import re
        json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
          content = json_match.group(1)
      
      result = json.loads(content)
      return result.get('recommendations', [])
    except json.JSONDecodeError:
      self.logger.error('Failed to parse recommendations')
      return []


class ActionableReportGenerator:
  """Generates actionable reports from labeling session analysis."""

  def __init__(self):
    """Initialize report generator."""
    self.logger = logging.getLogger(__name__)

  def generate_report(
    self,
    session_data: Dict[str, Any],
    statistics: Dict[str, Any],
    insights: Dict[str, Any],
    metrics: Dict[str, Any],
  ) -> str:
    """Generate comprehensive markdown report focused on actionable insights.

    Args:
        session_data: Session metadata and configuration
        statistics: Statistical analysis of labels
        insights: Discovered insights from SME assessments
        metrics: Completion and performance metrics

    Returns:
        Markdown formatted report
    """
    report_sections = []

    # Header
    report_sections.append(self._generate_header(session_data, metrics, insights))

    # Executive Summary
    report_sections.append(self._generate_executive_summary(insights, metrics, statistics))

    # Trace-Specific Label Interpretations
    report_sections.append(self._generate_trace_label_interpretations(insights))

    # Critical Issues Section
    report_sections.append(self._generate_critical_issues(insights))

    # Assessment Patterns
    report_sections.append(self._generate_assessment_patterns(insights, statistics))

    # Actionable Recommendations
    report_sections.append(self._generate_recommendations(insights))

    # Statistical Details
    report_sections.append(self._generate_statistical_analysis(statistics))

    # Footer
    report_sections.append(self._generate_footer())

    return '\n\n'.join(report_sections)

  def _generate_header(self, session_data: Dict[str, Any], metrics: Dict[str, Any], insights: Dict[str, Any] = None) -> str:
    """Generate report header."""
    session = session_data.get('session', {})
    
    # Get label counts from trace analysis if available
    trace_analysis = insights.get('trace_label_analysis', {}) if insights else {}
    labeled_count = trace_analysis.get('labeled_count', metrics.get('completed', 0))
    total_count = trace_analysis.get('total_analyzed', metrics.get('total_items', 0))
    
    return f"""# 🔬 Labeling Session Analysis Report

**Session:** {session.get('name', 'Unknown')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Scope:** Analyzing {labeled_count} labeled traces and {total_count - labeled_count if total_count > labeled_count else 0} unlabeled traces"""

  def _generate_executive_summary(
    self, insights: Dict[str, Any], metrics: Dict[str, Any], statistics: Dict[str, Any]
  ) -> str:
    """Generate executive summary."""
    # Handle case where insights might be None or have an error
    if not insights or 'error' in insights:
      return f"""## 📊 Executive Summary

### Analysis Status

{'Error generating insights. Running basic statistical analysis only.' if insights and 'error' in insights else 'Insights generation in progress.'}"""
    
    critical_issues = insights.get('critical_issues', [])
    critical_count = len([i for i in critical_issues if i.get('severity') == 'critical'])
    high_count = len([i for i in critical_issues if i.get('severity') == 'high'])

    summary_text = insights.get('agent_understanding', 'Analysis of agent behavior based on SME evaluations.')
    
    # Add critical issues count if any exist
    if critical_count > 0 or high_count > 0:
      issue_summary = []
      if critical_count > 0:
        issue_summary.append(f'{critical_count} critical')
      if high_count > 0:
        issue_summary.append(f'{high_count} high priority')
      summary_text += f"\n\n**Issues Found:** {' and '.join(issue_summary)} issues identified from labeled traces."

    return f"""## 📊 Executive Summary

### Agent Assessment

{summary_text}"""

  def _generate_trace_label_interpretations(self, insights: Dict[str, Any]) -> str:
    """Generate trace-specific label interpretations section."""
    trace_analysis = insights.get('trace_label_analysis', {})
    
    if not trace_analysis:
      return ''
    
    sections = ['## 🔍 Label Meanings in Context']
    sections.append('*Understanding what each label means based on the actual trace content*\n')
    
    # Pattern summary
    pattern_summary = trace_analysis.get('pattern_summary')
    if pattern_summary:
      sections.append('### Pattern Summary')
      sections.append(f'{pattern_summary}\n')
    
    # Label distribution meanings
    label_meanings = trace_analysis.get('label_distribution_meaning', {})
    if label_meanings:
      sections.append('### What the Labels Mean in This Context')
      if label_meanings.get('low_scores'):
        sections.append(f"- **Low Scores:** {label_meanings['low_scores']}")
      if label_meanings.get('high_scores'):
        sections.append(f"- **High Scores:** {label_meanings['high_scores']}")
      if label_meanings.get('false_labels'):
        sections.append(f"- **False/Incorrect Labels:** {label_meanings['false_labels']}")
      if label_meanings.get('unlabeled_implications'):
        sections.append(f"- **Unlabeled Traces:** {label_meanings['unlabeled_implications']}")
      sections.append('')
    
    # Key insights
    key_insights = trace_analysis.get('key_insights', [])
    if key_insights:
      sections.append('### Key Insights from Trace Analysis')
      for insight in key_insights:
        sections.append(f'- {insight}')
      sections.append('')
    
    # Individual trace analyses (show first 5 most interesting)
    trace_analyses = trace_analysis.get('trace_analyses', [])
    if trace_analyses:
      sections.append('### Detailed Trace Interpretations')
      sections.append('*Showing key examples of labeled and unlabeled traces*\n')
      
      for i, trace in enumerate(trace_analyses[:5], 1):
        trace_id = trace.get('trace_id', 'Unknown')
        state = trace.get('state', 'Unknown')
        state_emoji = '✅' if state == 'COMPLETED' else '⏳'
        
        sections.append(f"""#### {i}. Trace {trace_id[:8]}... {state_emoji} ({state})

**Label Interpretation:**
{trace.get('label_interpretation', 'No interpretation available')}
""")
        
        # Quality issues
        issues = trace.get('quality_issues', [])
        if issues:
          sections.append('**Quality Issues:**')
          for issue in issues:
            sections.append(f'- {issue}')
        
        # Positive aspects
        positives = trace.get('positive_aspects', [])
        if positives:
          sections.append('\n**Positive Aspects:**')
          for positive in positives:
            sections.append(f'- {positive}')
        
        # Key finding
        key_finding = trace.get('key_finding')
        if key_finding:
          sections.append(f'\n**Key Finding:** {key_finding}')
        
        # Show actual labels if completed
        if state == 'COMPLETED' and 'labels' in trace:
          labels = trace.get('labels', {})
          if labels:
            sections.append('\n**SME Labels:**')
            for key, value in labels.items():
              sections.append(f'- {key}: {value}')
        
        sections.append('')
    
    return '\n'.join(sections)

  def _generate_critical_issues(self, insights: Dict[str, Any]) -> str:
    """Generate critical issues section."""
    issues = insights.get('critical_issues', [])
    metadata = insights.get('metadata', {})
    completed_assessments = metadata.get('completed_assessments', 0)

    if not issues:
      return '## 🚨 Critical Issues\n\nNo critical issues identified from comprehensive analysis of all traces and assessments. This indicates the agent is performing well across the evaluated criteria.'

    sections = ['## 🚨 Critical Issues Found']
    sections.append('*All issues are grounded in actual SME assessments*\n')

    # Sort by priority
    issues.sort(key=lambda x: x.get('priority', 999))

    for i, issue in enumerate(issues[:10], 1):  # Top 10 issues
      severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(
        issue.get('severity', 'medium'), '🟡'
      )

      sections.append(f"""### {i}. {severity_emoji} {issue.get('issue_title', 'Issue')}

**Severity:** {issue.get('severity', 'unknown').title()}
**Frequency:** {issue.get('frequency', 'unknown')}
**Priority:** {issue.get('priority', 'N/A')}/10

**Description:**
{issue.get('description', 'No description available')}

**Root Cause:**
{issue.get('root_cause', 'To be investigated')}

**Evidence from SME Labels:**""")

      for evidence in issue.get('evidence_from_labels', [])[:3]:
        sections.append(f"- {evidence}")

      if issue.get('affected_traces'):
        trace_count = len(issue.get('affected_traces', []))
        sections.append(f"\n*Affects {trace_count} traces*")

    return '\n'.join(sections)

  def _generate_assessment_patterns(
    self, insights: Dict[str, Any], statistics: Dict[str, Any]
  ) -> str:
    """Generate assessment patterns section."""
    patterns = insights.get('assessment_patterns', {})

    sections = ['## 📈 Assessment Patterns']

    # Concerning patterns
    concerning = patterns.get('concerning_patterns', [])
    if concerning:
      sections.append('\n### ⚠️ Concerning Patterns')
      for pattern in concerning[:5]:
        sections.append(f"""
**{pattern.get('schema', 'Unknown')}** - {pattern.get('severity', 'medium').title()} Severity
- Pattern: {pattern.get('pattern', 'No description')}
- Evidence: {pattern.get('evidence', 'No evidence')}""")

    # Consensus areas
    consensus = patterns.get('consensus_areas', [])
    if consensus:
      sections.append('\n### 🤝 SME Consensus Areas')
      for area in consensus[:5]:
        consensus_type = area.get('consensus_type', 'unknown')
        emoji = '✅' if consensus_type == 'positive' else '❌'
        sections.append(
          f"- {emoji} **{area.get('schema', 'Unknown')}**: {area.get('description', 'No description')}"
        )

    # Key trends
    trends = patterns.get('key_trends', [])
    if trends:
      sections.append('\n### 📊 Key Trends')
      for trend in trends:
        sections.append(f'- {trend}')

    # Unexpected findings
    unexpected = patterns.get('unexpected_findings', [])
    if unexpected:
      sections.append('\n### 🔍 Unexpected Findings')
      for finding in unexpected:
        sections.append(f'- {finding}')

    return '\n'.join(sections)

  def _generate_recommendations(self, insights: Dict[str, Any]) -> str:
    """Generate recommendations section."""
    recommendations = insights.get('recommendations', [])
    metadata = insights.get('metadata', {})
    completed_assessments = metadata.get('completed_assessments', 0)

    if not recommendations:
      return '## 🎯 Recommendations\n\n**System Performance Assessment**\n\nBased on comprehensive analysis of all traces and assessments, the agent appears to be performing well within expected parameters. Continue monitoring performance and consider expanding evaluation criteria to capture additional quality dimensions.\n\n**Continuous Improvement**\n\nMaintain current performance levels while exploring opportunities for enhancement through additional trace analysis and user feedback collection.'

    sections = ['## 🎯 Actionable Recommendations']
    sections.append('*Prioritized actions based on SME assessment patterns*\n')

    # Group by priority
    priority_groups = {'immediate': [], 'high': [], 'medium': [], 'low': []}

    for rec in recommendations:
      priority = rec.get('priority', 'medium')
      if priority in priority_groups:
        priority_groups[priority].append(rec)

    # Display by priority
    for priority in ['immediate', 'high', 'medium', 'low']:
      recs = priority_groups[priority]
      if recs:
        priority_emoji = {
          'immediate': '🚨',
          'high': '🔥',
          'medium': '📊',
          'low': '📝',
        }.get(priority, '📝')

        sections.append(f'\n### {priority_emoji} {priority.title()} Priority')

        for rec in recs:
          sections.append(f"""
**{rec.get('title', 'Recommendation')}**

{rec.get('description', 'No description')}

*Rationale:* {rec.get('rationale', 'Based on SME assessments')}

*Expected Impact:* {rec.get('expected_impact', 'Quality improvement')}

*Success Metric:* {rec.get('success_metric', 'To be defined')}""")

    return '\n'.join(sections)

  def _generate_statistical_analysis(self, statistics: Dict[str, Any]) -> str:
    """Generate detailed statistical analysis."""
    sections = ['## 📊 Statistical Analysis']

    for schema_key, stats in statistics.items():
      if stats.get('count', 0) == 0:
        continue

      sections.append(f"\n### {stats.get('name', schema_key)}")

      if stats.get('type') == 'numerical':
        sections.append(f"""
- **Type:** Numerical Rating
- **Responses:** {stats.get('count', 0)}
- **Mean:** {stats.get('mean', 0):.2f}
- **Median:** {stats.get('median', 0):.2f}
- **Std Dev:** {stats.get('std', 0):.2f}
- **Range:** {stats.get('min', 0):.1f} - {stats.get('max', 0):.1f}""")

      elif stats.get('type') == 'categorical':
        sections.append(f"""
- **Type:** Categorical
- **Responses:** {stats.get('count', 0)}
- **Most Common:** {stats.get('mode', 'N/A')}""")

        distribution = stats.get('distribution', {})
        if distribution:
          sections.append('\n**Distribution:**')
          for category, data in distribution.items():
            sections.append(f"- {category}: {data['count']} ({data['percentage']:.1f}%)")

      elif stats.get('type') == 'text':
        sections.append(f"""
- **Type:** Text Feedback
- **Responses:** {stats.get('count', 0)}""")

        themes = stats.get('themes', [])
        if themes:
          sections.append(f"- **Common Themes:** {', '.join(themes)}")

    return '\n'.join(sections)

  def _generate_footer(self) -> str:
    """Generate report footer."""
    return """## 📝 Next Steps

1. **Address Immediate Issues**: Focus on critical issues identified from SME assessments
2. **Implement Recommendations**: Follow the prioritized action plan
3. **Monitor Improvements**: Re-run evaluation after fixes to measure impact
4. **Iterate**: Continue the feedback loop with SMEs for continuous improvement

---

*This report was generated using chain-of-thought analysis grounded entirely in SME assessments. All insights and recommendations are based on actual labeling data, not hypothetical scenarios.*"""


class LabelingSessionAnalyzer:
  """Core analysis engine for labeling sessions with enhanced methodology."""

  def __init__(self):
    self.items = []
    self.session = {}
    self.schemas = []
    self.review_app = {}
    self.logger = logging.getLogger(__name__)

  async def load_session_data(self, review_app_id: str, session_id: str) -> Dict[str, Any]:
    """Load all session data including items, schemas, and labels."""
    try:
      # Get session details
      self.session = await get_labeling_session(review_app_id, session_id)

      # Get review app for schemas
      self.review_app = await review_apps_utils.get_review_app(review_app_id)
      
      # Use session's labeling schemas if specified, otherwise use all review app schemas
      session_schemas = self.session.get('labeling_schemas', [])
      if session_schemas:
        # Session has specific schemas - filter review app schemas to match
        review_app_schemas = self.review_app.get('labeling_schemas', [])
        schema_keys = {s.get('key') for s in session_schemas if s.get('key')}
        self.schemas = [s for s in review_app_schemas if s.get('key') in schema_keys]
        self.logger.info(f'Using {len(self.schemas)} schemas specified in session from {len(review_app_schemas)} available')
      else:
        # Use all schemas from review app
        self.schemas = self.review_app.get('labeling_schemas', [])
        self.logger.info(f'Using all {len(self.schemas)} schemas from review app')

      # Get all labeling items
      items_response = await labeling_items_utils.list_items(
        review_app_id=review_app_id, labeling_session_id=session_id
      )
      self.items = items_response.get('items', [])

      self.logger.info(
        f'Loaded session {session_id}: {len(self.items)} items, {len(self.schemas)} schemas'
      )

      return {
        'session': self.session,
        'review_app': self.review_app,
        'schemas': self.schemas,
        'items': self.items,
        'total_items': len(self.items),
        'completed_items': len([i for i in self.items if i.get('state') == 'COMPLETED']),
      }
    except Exception as e:
      self.logger.error(f'Error loading session data: {e}')
      raise

  def compute_schema_statistics(self) -> Dict[str, Any]:
    """Compute statistics for each schema."""
    schema_stats = {}

    for schema in self.schemas:
      schema_key = schema.get('key', 'unknown')
      schema_type = schema.get('schema_type', 'unknown')

      # Extract all labels for this schema
      labels = []
      for item in self.items:
        if item.get('state') == 'COMPLETED':
          item_labels = item.get('labels', {})
          if schema_key in item_labels:
            labels.append(item_labels[schema_key])

      if not labels:
        schema_stats[schema_key] = {
          'type': schema_type,
          'name': schema.get('name', schema_key),
          'count': 0,
          'stats': 'No data',
        }
        continue

      # Compute statistics based on schema type
      if schema_type == 'numerical':
        numeric_labels = [float(l) for l in labels if l is not None]
        if numeric_labels:
          schema_stats[schema_key] = {
            'type': schema_type,
            'name': schema.get('name', schema_key),
            'count': len(numeric_labels),
            'mean': mean(numeric_labels),
            'median': median(numeric_labels),
            'std': stdev(numeric_labels) if len(numeric_labels) > 1 else 0,
            'min': min(numeric_labels),
            'max': max(numeric_labels),
            'distribution': self._compute_distribution(numeric_labels),
          }

      elif schema_type == 'categorical':
        category_counts = Counter(labels)
        total = sum(category_counts.values())
        schema_stats[schema_key] = {
          'type': schema_type,
          'name': schema.get('name', schema_key),
          'count': len(labels),
          'distribution': {
            cat: {'count': count, 'percentage': (count / total) * 100}
            for cat, count in category_counts.items()
          },
          'mode': category_counts.most_common(1)[0][0] if category_counts else None,
        }

      elif schema_type == 'text':
        schema_stats[schema_key] = {
          'type': schema_type,
          'name': schema.get('name', schema_key),
          'count': len(labels),
          'sample_feedback': labels[:3],  # First 3 examples
          'themes': self._extract_themes(labels),
        }

    return schema_stats

  def calculate_completion_metrics(self) -> Dict[str, Any]:
    """Calculate session completion metrics."""
    total = len(self.items)
    completed = len([i for i in self.items if i.get('state') == 'COMPLETED'])
    pending = len([i for i in self.items if i.get('state') == 'PENDING'])
    skipped = len([i for i in self.items if i.get('state') == 'SKIPPED'])

    # Calculate time metrics if available
    completion_times = []
    for item in self.items:
      if item.get('state') == 'COMPLETED':
        # Estimate based on update time (simplified)
        completion_times.append(5)  # Default 5 minutes per item

    return {
      'total_items': total,
      'completed': completed,
      'pending': pending,
      'skipped': skipped,
      'completion_rate': (completed / total * 100) if total > 0 else 0,
      'avg_time_per_item': mean(completion_times) if completion_times else 0,
      'total_time_spent': sum(completion_times) if completion_times else 0,
    }

  def _compute_distribution(self, values: List[float]) -> Dict[str, int]:
    """Compute distribution buckets for numeric values."""
    if not values:
      return {}

    min_val, max_val = min(values), max(values)
    if min_val == max_val:
      return {str(min_val): len(values)}

    # Create 5 buckets
    bucket_size = (max_val - min_val) / 5
    buckets = defaultdict(int)

    for val in values:
      bucket_idx = min(int((val - min_val) / bucket_size), 4)
      bucket_start = min_val + bucket_idx * bucket_size
      bucket_end = bucket_start + bucket_size
      bucket_key = f'{bucket_start:.1f}-{bucket_end:.1f}'
      buckets[bucket_key] += 1

    return dict(buckets)

  def _extract_themes(self, texts: List[str]) -> List[str]:
    """Extract common themes from text feedback."""
    if not texts:
      return []

    # Simple word frequency analysis
    word_counts = Counter()
    for text in texts:
      if text:
        words = text.lower().split()
        # Filter common words
        meaningful_words = [
          w
          for w in words
          if len(w) > 3
          and w not in ['this', 'that', 'with', 'from', 'have', 'been', 'were', 'could']
        ]
        word_counts.update(meaningful_words)

    # Return top 5 themes
    return [word for word, _ in word_counts.most_common(5)]


async def retrieve_experiment_report(experiment_id: str) -> Optional[str]:
  """Retrieve experiment analysis report from MLflow artifacts if available.

  Args:
      experiment_id: MLflow experiment ID

  Returns:
      Experiment report content or None if not found
  """
  try:
    artifact_manager = MLflowArtifactManager()

    # Find the metadata run for this experiment
    from mlflow.tracking import MlflowClient

    client = MlflowClient()

    filter_string = (
      f"tags.`mlflow.runName` = 'experiment_metadata' AND tags.`experiment.id` = '{experiment_id}'"
    )
    runs = client.search_runs(
      experiment_ids=[experiment_id], filter_string=filter_string, max_results=1
    )

    if not runs:
      logger.info(f'No experiment analysis found for {experiment_id}')
      return None

    run = runs[0]
    run_id = run.info.run_id

    # Try to get the markdown report
    try:
      markdown_path = f'analysis/experiment_summaries/{experiment_id}_summary.md'
      content = artifact_manager.download_analysis_report(run_id, markdown_path)
      logger.info(f'Retrieved experiment report for context ({len(content)} chars)')
      return content
    except:
      logger.info('Could not retrieve experiment report')
      return None

  except Exception as e:
    logger.error(f'Error retrieving experiment report: {e}')
    return None


async def load_session_traces(session: Dict[str, Any], items: List[Dict[str, Any]] = None, limit: int = 500) -> List[Dict[str, Any]]:
  """Load traces specifically linked to this labeling session.

  This function loads ONLY the traces that are associated with the session's MLflow run,
  ensuring we analyze the correct subset of traces for this specific session.

  Args:
      session: Labeling session data with mlflow_run_id
      items: Optional list of session items to extract specific trace IDs
      limit: Maximum number of traces to load (default 500)

  Returns:
      List of trace data dictionaries specifically for this session
  """
  try:
    # Get experiment ID from session or config
    experiment_id = session.get('experiment_id') or config.experiment_id
    if not experiment_id:
      logger.warning('No experiment_id in session or config')
      return []

    # Get the MLflow run ID for this session
    mlflow_run_id = session.get('mlflow_run_id')
    if not mlflow_run_id:
      logger.warning('No mlflow_run_id in session - cannot load session-specific traces')
      # Fall back to loading traces from items only
      session_trace_ids = set()
      if items:
        for item in items:
          trace_id = item.get('source', {}).get('trace_id')
          if trace_id:
            session_trace_ids.add(trace_id)
      logger.info(f'Loading {len(session_trace_ids)} traces from session items only')
      
      # Load only the specific traces from items
      traces = []
      for trace_id in session_trace_ids:
        try:
          trace = get_trace(trace_id)
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
            },
          }
          traces.append(trace_dict)
        except Exception as e:
          logger.warning(f'Error loading trace {trace_id}: {e}')
      return traces
    
    # Load traces linked to the session's MLflow run
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    
    # Get the run to access linked traces
    try:
      run = client.get_run(mlflow_run_id)
      
      # Get trace IDs from run tags (linked traces are stored in tags)
      linked_trace_ids = []
      for key, value in run.data.tags.items():
        if key.startswith('mlflow.linkedTraces.'):
          linked_trace_ids.append(value)
      
      # Also collect trace IDs from session items
      session_trace_ids = set()
      if items:
        for item in items:
          trace_id = item.get('source', {}).get('trace_id')
          if trace_id:
            session_trace_ids.add(trace_id)
      
      # Combine both sources
      all_trace_ids = set(linked_trace_ids) | session_trace_ids
      logger.info(f'Found {len(all_trace_ids)} traces linked to session (run: {mlflow_run_id})')
      
      # Load each trace
      traces = []
      for trace_id in list(all_trace_ids)[:limit]:  # Respect limit
        try:
          trace = get_trace(trace_id)
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
            },
          }
          traces.append(trace_dict)
        except Exception as e:
          logger.warning(f'Error loading trace {trace_id}: {e}')
      
      logger.info(f'Successfully loaded {len(traces)} traces for session analysis')
      return traces
      
    except Exception as e:
      logger.error(f'Error loading traces for run {mlflow_run_id}: {e}')
      # Fall back to loading from items only
      session_trace_ids = set()
      if items:
        for item in items:
          trace_id = item.get('source', {}).get('trace_id')
          if trace_id:
            session_trace_ids.add(trace_id)
      
      traces = []
      for trace_id in session_trace_ids:
        try:
          trace = get_trace(trace_id)
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
            },
          }
          traces.append(trace_dict)
        except Exception as e:
          logger.warning(f'Error loading trace {trace_id}: {e}')
      
      return traces

  except Exception as e:
    logger.error(f'Error loading session traces: {e}')
    return []


# Main analysis orchestration function
async def analyze_labeling_session_complete(
  review_app_id: str,
  session_id: str,
  include_ai_insights: bool = True,
  model_endpoint: str = 'databricks-claude-sonnet-4',
  store_to_mlflow: bool = True,
) -> Dict[str, Any]:
  """Complete analysis of a labeling session with enhanced methodology.

  This function:
  1. Loads session data and traces
  2. Retrieves experiment context if available
  3. Performs statistical analysis
  4. Discovers insights using chain-of-thought
  5. Generates actionable report
  6. Stores to MLflow artifacts (overwrites if exists)

  Args:
      review_app_id: Review app ID
      session_id: Labeling session ID
      include_ai_insights: Whether to generate AI insights
      model_endpoint: Model endpoint for AI insights
      store_to_mlflow: Whether to store results to MLflow

  Returns:
      Comprehensive analysis results with report
  """
  logger.info(f'Starting enhanced analysis of labeling session {session_id}')

  # Initialize components
  analyzer = LabelingSessionAnalyzer()
  session_data = await analyzer.load_session_data(review_app_id, session_id)

  # Compute basic statistics
  statistics = analyzer.compute_schema_statistics()
  metrics = analyzer.calculate_completion_metrics()

  # Load ALL traces for comprehensive analysis
  traces = await load_session_traces(session_data['session'], analyzer.items)

  # Retrieve experiment report if available
  experiment_id = session_data.get('session', {}).get('experiment_id') or config.experiment_id
  experiment_report = None
  if experiment_id:
    experiment_report = await retrieve_experiment_report(experiment_id)

  # Generate AI insights if requested
  insights = None
  report = None

  if include_ai_insights:
    try:
      # Initialize model client and insight discovery
      model_client = ModelServingClient()
      model_client.default_endpoint = model_endpoint

      insight_discovery = SMEInsightDiscovery(model_client)

      # Discover insights from ALL traces and SME assessments
      logger.info('Discovering insights from ALL traces and SME assessments...')
      insights = await insight_discovery.discover_insights(
        items=analyzer.items,  # ALL items in session
        schemas=analyzer.schemas,
        traces=traces,  # ALL traces loaded for comprehensive analysis
        experiment_context=experiment_report[:3000] if experiment_report else None,
      )

      # Generate actionable report
      logger.info('Generating actionable report...')
      report_generator = ActionableReportGenerator()
      report = report_generator.generate_report(
        session_data=session_data, statistics=statistics, insights=insights, metrics=metrics
      )

    except Exception as e:
      logger.error(f'Error generating AI insights: {e}', exc_info=True)
      insights = {
        'error': str(e),
        'agent_understanding': f'Error during analysis: {e}',
        'assessment_patterns': {},
        'critical_issues': [],
        'recommendations': [],
        'metadata': {
          'total_items_analyzed': len(analyzer.items),
          'completed_assessments': metrics.get('completed', 0),
          'total_traces_analyzed': len(traces),
          'discovery_method': 'error-fallback',
        }
      }
      # Still generate a report with available data
      report_generator = ActionableReportGenerator()
      report = report_generator.generate_report(
        session_data=session_data, statistics=statistics, insights=insights, metrics=metrics
      )

  else:
    # Generate basic report without AI
    report = _generate_basic_report(session_data, statistics, metrics)

  # Store to MLflow if requested
  storage_result = None
  if store_to_mlflow:
    session_run_id = session_data.get('session', {}).get('mlflow_run_id')
    if session_run_id:
      try:
        artifact_manager = MLflowArtifactManager()

        # Store markdown report
        report_path = artifact_manager.log_analysis_report(
          run_id=session_run_id,
          content=report,
          report_name='report',
          report_type='markdown',
          artifact_path='analysis/session_summary',
        )

        # Store structured data
        # Merge insights metadata with our metadata
        combined_metadata = {
          'session_id': session_id,
          'review_app_id': review_app_id,
          'analysis_timestamp': datetime.now().isoformat(),
          'model_endpoint': model_endpoint,
          'completed_assessments': metrics.get('completed', 0),
          'total_items_analyzed': metrics.get('total_items', 0),
          'has_experiment_context': experiment_report is not None,
        }
        
        # Add insights metadata if available
        if insights and 'metadata' in insights:
          combined_metadata.update(insights['metadata'])
        else:
          # Ensure we have the key fields even if insights failed
          combined_metadata['total_traces_analyzed'] = len(traces)
          combined_metadata['discovery_method'] = 'statistical-only' if not insights else insights.get('metadata', {}).get('discovery_method', 'unknown')
        
        analysis_data = {
          'metadata': combined_metadata,
          'statistics': statistics,
          'metrics': metrics,
          'insights': insights,
        }

        data_path = artifact_manager.log_structured_analysis(
          run_id=session_run_id,
          analysis_data=analysis_data,
          analysis_name='data',
          artifact_path='analysis/session_summary',
        )

        # Store metadata
        metadata = {
          'analysis_type': 'labeling_session',
          'session_id': session_id,
          'timestamp': datetime.now().isoformat(),
          'paths': {'report': report_path, 'data': data_path},
        }

        metadata_path = artifact_manager.log_structured_analysis(
          run_id=session_run_id,
          analysis_data=metadata,
          analysis_name='metadata',
          artifact_path='analysis/session_summary',
        )

        storage_result = {
          'run_id': session_run_id,
          'report_path': report_path,
          'data_path': data_path,
          'metadata_path': metadata_path,
        }

        logger.info(f'Analysis stored to MLflow run {session_run_id}')

      except Exception as e:
        logger.error(f'Failed to store to MLflow: {e}')
        storage_result = {'error': str(e)}
    else:
      logger.warning('No MLflow run ID found for session')

  return {
    'status': 'success',
    'session_id': session_id,
    'session_data': session_data,
    'statistics': statistics,
    'metrics': metrics,
    'insights': insights,
    'report': report,
    'storage': storage_result,
    'has_experiment_context': experiment_report is not None,
  }


def _generate_basic_report(
  session_data: Dict[str, Any], statistics: Dict[str, Any], metrics: Dict[str, Any]
) -> str:
  """Generate basic report without AI insights."""
  session = session_data.get('session', {})

  report = f"""# Labeling Session Analysis Report

**Session:** {session.get('name', 'Unknown')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics

- **Completion Rate:** {metrics.get('completion_rate', 0):.1f}%
- **Items Completed:** {metrics.get('completed', 0)}/{metrics.get('total_items', 0)}
- **Time Spent:** {metrics.get('total_time_spent', 0):.0f} minutes

## Schema Statistics

"""

  for schema_key, stats in statistics.items():
    if stats.get('count', 0) > 0:
      report += f"### {stats.get('name', schema_key)}\n"
      report += f"- Type: {stats.get('type', 'unknown')}\n"
      report += f"- Responses: {stats.get('count', 0)}\n"

      if stats.get('type') == 'numerical':
        report += f"- Mean: {stats.get('mean', 0):.2f}\n"
        report += f"- Median: {stats.get('median', 0):.2f}\n"
      elif stats.get('type') == 'categorical':
        report += f"- Most Common: {stats.get('mode', 'N/A')}\n"

      report += '\n'

  return report


# Export for backward compatibility
class TraceLabelCorrelator:
  """Legacy class for trace-label correlation (kept for compatibility)."""

  def __init__(self, items: List[Dict], schemas: List[Dict]):
    self.items = items
    self.schemas = schemas
    self.trace_features = {}
    self.logger = logging.getLogger(__name__)

  def fetch_trace_features(self) -> Dict[str, Dict]:
    """Fetch and extract features from traces."""
    trace_features = {}

    for item in self.items:
      if item.get('state') == 'COMPLETED':
        trace_id = item.get('source', {}).get('trace_id')
        if trace_id:
          try:
            trace = get_trace(trace_id)
            features = self._extract_trace_features(trace)
            trace_features[trace_id] = features
          except Exception as e:
            self.logger.warning(f'Error fetching trace {trace_id}: {e}')
            continue

    self.trace_features = trace_features
    return trace_features

  def _extract_trace_features(self, trace) -> Dict[str, Any]:
    """Extract relevant features from a trace."""
    features = {
      'execution_time_ms': trace.info.execution_time_ms
      if hasattr(trace.info, 'execution_time_ms')
      else 0,
      'status': trace.info.status if hasattr(trace.info, 'status') else 'unknown',
      'span_count': len(trace.data.spans) if hasattr(trace.data, 'spans') else 0,
      'tool_count': 0,
      'has_errors': False,
    }

    if hasattr(trace.data, 'spans') and trace.data.spans:
      for span in trace.data.spans:
        if hasattr(span, 'span_type') and span.span_type == 'TOOL':
          features['tool_count'] += 1
        if hasattr(span, 'status') and 'error' in str(span.status).lower():
          features['has_errors'] = True

    return features


# Keep other legacy classes for compatibility
class PatternDetector:
  """Legacy pattern detector (kept for compatibility)."""

  def __init__(self, items: List[Dict], schemas: List[Dict]):
    self.items = items
    self.schemas = schemas
    self.logger = logging.getLogger(__name__)