"""Open-ended Issue Discovery Module

Uses LLM to discover quality issues in traces without predefined categories.
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IssueDiscovery:
    """Discovers quality issues in traces using open-ended LLM analysis."""
    
    def __init__(self, model_client):
        """Initialize with model serving client."""
        self.model_client = model_client
        self.logger = logging.getLogger(__name__)
    
    async def discover_issues(
        self, 
        traces: List[Dict[str, Any]], 
        experiment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover quality issues using chain-of-thought LLM analysis.
        
        Args:
            traces: List of trace data to analyze
            experiment_info: Experiment metadata for context
            
        Returns:
            Dictionary with discovered issues and full trace mappings
        """
        self.logger.info(f"Starting open-ended issue discovery for {len(traces)} traces")
        
        # Step 1: Understand what the agent does
        agent_understanding = self._understand_agent_purpose(traces, experiment_info)
        
        # Step 2: Discover issue categories
        discovered_categories = self._discover_issue_categories(traces, agent_understanding)
        
        # Step 3: Systematic analysis with ALL trace IDs
        comprehensive_issues = self._analyze_all_traces(
            traces, 
            discovered_categories, 
            agent_understanding
        )
        
        # Step 4: Aggregate and organize
        organized_issues = self._organize_issues(comprehensive_issues)
        
        return {
            'agent_understanding': agent_understanding,
            'discovered_categories': discovered_categories,
            'issues': organized_issues,
            'metadata': {
                'total_traces_analyzed': len(traces),
                'unique_issue_types': len(organized_issues),
                'discovery_method': 'open-ended-llm'
            }
        }
    
    def _understand_agent_purpose(
        self, 
        traces: List[Dict[str, Any]], 
        experiment_info: Dict[str, Any]
    ) -> str:
        """First understand what this agent is supposed to do."""
        
        # Sample a few traces for understanding
        sample_traces = traces[:5] if len(traces) > 5 else traces
        
        # Extract requests and responses
        interactions = []
        for trace in sample_traces:
            interaction = {
                'request': trace.get('data', {}).get('request', 'N/A'),
                'response': trace.get('data', {}).get('response', 'N/A'),
                'tools_used': self._extract_tool_names(trace)
            }
            interactions.append(interaction)
        
        prompt = f"""
        ## Chain of Thought: Understanding the Agent
        
        Experiment: {experiment_info.get('name', 'Unknown')}
        
        Sample interactions:
        {json.dumps(interactions, indent=2)}
        
        Based on these interactions, describe:
        1. What type of agent is this? (e.g., SQL assistant, code generator, customer service, etc.)
        2. What are its primary capabilities?
        3. What tools/functions does it use?
        4. What is the expected behavior for this type of agent?
        5. What domain-specific requirements might apply?
        
        Provide a concise summary of the agent's purpose and expected behavior.
        """
        
        response = self.model_client.query_endpoint(
            endpoint_name=self.model_client.default_endpoint,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.get('content', 'Unknown agent type')
    
    def _discover_issue_categories(
        self, 
        traces: List[Dict[str, Any]], 
        agent_understanding: str
    ) -> List[Dict[str, Any]]:
        """Discover what types of issues exist in this specific data."""
        
        # Sample more traces for discovery
        sample_traces = traces[:20] if len(traces) > 20 else traces
        
        # Prepare trace summaries
        trace_summaries = []
        for trace in sample_traces:
            summary = {
                'trace_id': trace.get('info', {}).get('trace_id'),
                'status': trace.get('info', {}).get('status'),
                'request_preview': str(trace.get('data', {}).get('request', ''))[:200],
                'response_preview': str(trace.get('data', {}).get('response', ''))[:200],
                'tool_errors': self._extract_tool_errors(trace),
                'spans_count': len(trace.get('data', {}).get('spans', []))
            }
            trace_summaries.append(summary)
        
        prompt = f"""
        ## Chain of Thought: Issue Discovery
        
        Agent Understanding:
        {agent_understanding}
        
        Trace Data:
        {json.dumps(trace_summaries, indent=2)}
        
        Analyze these traces to discover quality issues. DO NOT use a predefined list.
        Instead, identify issues specific to THIS agent and THIS data.
        
        For each distinct issue type you discover:
        1. Give it a descriptive name
        2. Explain what's wrong
        3. Explain why it matters for this specific agent
        4. List specific trace IDs that exhibit this issue
        5. Provide example snippets showing the problem
        
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
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.get('content', '{}'))
            return result.get('discovered_issue_types', [])
        except json.JSONDecodeError:
            self.logger.error("Failed to parse discovery response")
            return []
    
    def _analyze_all_traces(
        self, 
        traces: List[Dict[str, Any]], 
        discovered_categories: List[Dict[str, Any]],
        agent_understanding: str
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
                'tool_count': len(self._extract_tool_names(trace))
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
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.get('content', '{}'))
            return result.get('comprehensive_issues', [])
        except json.JSONDecodeError:
            self.logger.error("Failed to parse comprehensive analysis")
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
                    f"Issue {issue.get('issue_type')}: "
                    f"stated {stated_count} traces but found {actual_count} IDs"
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
                'evaluation_question': issue.get('evaluation_question', '')
            }
            
            organized.append(organized_issue)
        
        # Sort by severity and affected traces
        organized.sort(
            key=lambda x: (
                {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x['severity']],
                x['affected_traces']
            ),
            reverse=True
        )
        
        return organized
    
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