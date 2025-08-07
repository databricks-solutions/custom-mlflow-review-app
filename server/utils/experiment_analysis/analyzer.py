"""Main Experiment Analyzer Module

Orchestrates the complete analysis pipeline with chain-of-thought reasoning.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..mlflow_artifact_utils import MLflowArtifactManager
from ..mlflow_utils import get_experiment, search_traces
from ..model_serving_utils import ModelServingClient
from .issue_discovery import IssueDiscovery
from .schema_generator import SchemaGenerator
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ExperimentAnalyzer:
    """Main orchestrator for experiment analysis."""
    
    def __init__(self, model_endpoint: str = 'databricks-claude-sonnet-4'):
        """Initialize analyzer with model endpoint."""
        self.model_client = ModelServingClient()
        self.model_client.default_endpoint = model_endpoint
        self.issue_discovery = IssueDiscovery(self.model_client)
        self.schema_generator = SchemaGenerator()
        self.report_generator = ReportGenerator()
        self.artifact_manager = MLflowArtifactManager()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_experiment(
        self,
        experiment_id: str,
        focus: str = 'comprehensive',
        trace_sample_size: int = 50
    ) -> Dict[str, Any]:
        """Run complete experiment analysis pipeline.
        
        Args:
            experiment_id: MLflow experiment ID
            focus: Analysis focus (comprehensive, quality, etc.)
            trace_sample_size: Number of traces to analyze
            
        Returns:
            Complete analysis with report, issues, and schemas
        """
        try:
            self.logger.info(f"Starting comprehensive analysis of experiment {experiment_id}")
            
            # Step 1: Gather experiment data
            self.logger.info("Step 1: Gathering experiment data...")
            experiment_data = await self._gather_experiment_data(experiment_id, trace_sample_size)
            
            # Step 2: Discover issues using open-ended LLM analysis
            self.logger.info("Step 2: Discovering issues with chain-of-thought...")
            discovery_result = await self.issue_discovery.discover_issues(
                experiment_data['traces'],
                experiment_data['experiment_info']
            )
            
            # Step 3: Generate schemas based on discovered issues
            self.logger.info("Step 3: Generating evaluation schemas...")
            schemas = self.schema_generator.generate_schemas_for_issues(
                discovery_result['issues'],
                discovery_result['agent_understanding']
            )
            
            # Step 4: Generate comprehensive report
            self.logger.info("Step 4: Generating analysis report...")
            report = self.report_generator.generate_report(
                experiment_data,
                discovery_result,
                schemas
            )
            
            # Step 5: Structure complete response
            self.logger.info("Step 5: Structuring final analysis...")
            structured_analysis = self._structure_analysis(
                experiment_data,
                discovery_result,
                schemas,
                report
            )
            
            # Step 6: Store to MLflow artifacts
            self.logger.info("Step 6: Storing analysis to MLflow...")
            storage_result = await self._store_analysis(
                experiment_id,
                structured_analysis
            )
            
            structured_analysis['storage'] = storage_result
            
            self.logger.info("Analysis complete!")
            return structured_analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'experiment_id': experiment_id
            }
    
    async def _gather_experiment_data(
        self, 
        experiment_id: str, 
        sample_size: int
    ) -> Dict[str, Any]:
        """Gather all necessary experiment data."""
        
        # Get experiment metadata
        experiment_info = get_experiment(experiment_id)
        
        # Get all traces (up to sample_size)
        raw_traces = search_traces(
            experiment_ids=[experiment_id],
            max_results=sample_size,
            order_by=['timestamp_ms DESC']
        )
        
        # Convert traces to analyzable format
        traces = []
        for trace in raw_traces:
            try:
                trace_dict = {
                    'info': {
                        'trace_id': trace.info.trace_id,
                        'experiment_id': trace.info.experiment_id,
                        'timestamp_ms': trace.info.timestamp_ms,
                        'execution_time_ms': trace.info.execution_time_ms,
                        'status': trace.info.status,
                        'request_id': getattr(trace.info, 'request_id', None),
                    },
                    'data': {
                        'request': getattr(trace.data, 'request', None),
                        'response': getattr(trace.data, 'response', None),
                        'spans': []
                    }
                }
                
                # Extract spans
                if trace.data and trace.data.spans:
                    for span in trace.data.spans:
                        span_dict = {
                            'span_id': span.span_id,
                            'name': span.name,
                            'span_type': span.span_type,
                            'parent_id': span.parent_id,
                            'start_time_ms': span.start_time_ms,
                            'end_time_ms': span.end_time_ms,
                            'status': span.status,
                            'inputs': span.inputs,
                            'outputs': span.outputs,
                        }
                        trace_dict['data']['spans'].append(span_dict)
                
                traces.append(trace_dict)
                
            except Exception as e:
                self.logger.warning(f"Error processing trace {trace.info.trace_id}: {e}")
                continue
        
        self.logger.info(f"Gathered {len(traces)} traces for analysis")
        
        return {
            'experiment_info': {
                'experiment_id': experiment_info.experiment_id,
                'name': experiment_info.name,
                'artifact_location': experiment_info.artifact_location,
                'lifecycle_stage': experiment_info.lifecycle_stage,
                'creation_time': experiment_info.creation_time,
                'last_update_time': experiment_info.last_update_time,
                'tags': experiment_info.tags
            },
            'traces': traces,
            'total_traces': len(traces),
            'sample_size_requested': sample_size
        }
    
    def _structure_analysis(
        self,
        experiment_data: Dict[str, Any],
        discovery_result: Dict[str, Any],
        schemas: List[Dict[str, Any]],
        report: str
    ) -> Dict[str, Any]:
        """Structure the complete analysis response."""
        
        # Calculate summary statistics
        total_issues = len(discovery_result['issues'])
        critical_issues = len([i for i in discovery_result['issues'] if i['severity'] == 'critical'])
        high_issues = len([i for i in discovery_result['issues'] if i['severity'] == 'high'])
        
        # Prepare issues with ALL trace IDs
        issues_with_full_traces = []
        for issue in discovery_result['issues']:
            issue_data = {
                'issue_type': issue['issue_type'],
                'severity': issue['severity'],
                'title': issue['title'],
                'description': issue['description'],
                'affected_traces': issue['affected_traces'],
                'example_traces': issue['example_traces'],  # For UI preview
                'all_trace_ids': issue.get('all_trace_ids', []),  # ALL affected traces
                'problem_snippets': issue.get('problem_snippets', [])
            }
            issues_with_full_traces.append(issue_data)
        
        # Prepare schemas with trace mappings
        schemas_with_traces = []
        for schema in schemas:
            schema_data = {
                **schema,
                'all_affected_traces': schema.get('all_affected_traces', []),
                'affected_trace_count': schema.get('affected_trace_count', 0)
            }
            schemas_with_traces.append(schema_data)
        
        return {
            'status': 'success',
            'experiment_id': experiment_data['experiment_info']['experiment_id'],
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'model_endpoint': self.model_client.default_endpoint,
                'traces_analyzed': experiment_data['total_traces'],
                'total_issues_found': total_issues,
                'critical_issues': critical_issues,
                'high_priority_issues': high_issues,
                'schemas_generated': len(schemas)
            },
            'executive_summary': {
                'agent_type': discovery_result['agent_understanding'],
                'total_traces_analyzed': experiment_data['total_traces'],
                'critical_issues_found': critical_issues,
                'high_priority_issues': high_issues,
                'recommended_schemas': len(schemas),
                'discovery_method': 'open-ended-chain-of-thought'
            },
            'content': report,  # Markdown report
            'raw_sme_analysis': {
                'agent_understanding': discovery_result['agent_understanding'],
                'discovered_categories': discovery_result.get('discovered_categories', []),
                'issue_detection': {
                    'detected_issues': issues_with_full_traces,
                    'summary': {
                        'total_issues': total_issues,
                        'by_severity': {
                            'critical': critical_issues,
                            'high': high_issues,
                            'medium': len([i for i in discovery_result['issues'] if i['severity'] == 'medium']),
                            'low': len([i for i in discovery_result['issues'] if i['severity'] == 'low'])
                        }
                    }
                },
                'schema_recommendations': {
                    'recommended_schemas': schemas_with_traces
                }
            },
            'detected_issues': issues_with_full_traces,  # For UI
            'schemas_with_label_types': schemas_with_traces  # For UI
        }
    
    async def _store_analysis(
        self,
        experiment_id: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Store analysis results to MLflow artifacts."""
        
        try:
            # Store both markdown and JSON
            storage_result = self.artifact_manager.store_experiment_summary(
                experiment_id=experiment_id,
                summary_content=analysis['content'],
                summary_data=analysis,
                tags={
                    'analysis.type': 'comprehensive',
                    'analysis.method': 'open-ended-discovery',
                    'analysis.timestamp': analysis['metadata']['analysis_timestamp']
                }
            )
            
            return storage_result
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis: {e}")
            return {'error': str(e)}