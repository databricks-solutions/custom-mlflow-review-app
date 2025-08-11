"""Experiment summary endpoints for AI-generated analysis stored in MLflow artifacts."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel

from server.utils.ai_analysis_utils import AIExperimentAnalyzer
from server.utils.mlflow_artifact_utils import MLflowArtifactManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/experiment-summary', tags=['Experiment Summary'])


class TriggerAnalysisRequest(BaseModel):
  """Request to trigger AI analysis of an experiment."""

  experiment_id: str
  focus: str = 'comprehensive'
  trace_sample_size: int = 50
  model_endpoint: str = 'databricks-claude-sonnet-4'


class AnalysisStatus(BaseModel):
  """Status of an analysis request."""

  experiment_id: str
  status: str  # 'pending', 'running', 'completed', 'failed'
  message: Optional[str] = None
  run_id: Optional[str] = None


# Store for tracking analysis status (in production, use a database)
analysis_status_store: Dict[str, AnalysisStatus] = {}


@router.get('/{experiment_id}')
async def get_experiment_summary(experiment_id: str) -> dict:
  """Get experiment summary from MLflow artifacts.

  Args:
      experiment_id: The MLflow experiment ID

  Returns:
      Dictionary containing summary content and metadata
  """
  try:
    artifact_manager = MLflowArtifactManager()
    client = MlflowClient()

    # Find the metadata run for this experiment
    filter_string = (
      f"tags.`mlflow.runName` = 'experiment_metadata' AND tags.`experiment.id` = '{experiment_id}'"
    )
    runs = client.search_runs(
      experiment_ids=[experiment_id],
      filter_string=filter_string,
      max_results=1,
      order_by=['start_time DESC'],
    )

    if not runs:
      # Fallback to local file system for backward compatibility
      project_root = Path(__file__).parent.parent.parent.parent
      reports_dir = project_root / 'reports' / 'experiments'
      summary_file = reports_dir / f'{experiment_id}_summary.md'

      if summary_file.exists():
        try:
          with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
          return {
            'has_summary': True,
            'content': content,
            'source': 'local_file',
            'message': 'Summary from local file. Run new analysis to get MLflow-stored version.',
          }
        except:
          pass

      return {
        'has_summary': False,
        'content': None,
        'message': 'No analysis found. Click "Run AI Analysis" to generate comprehensive quality analysis.',
        'schemas_with_label_types': None,
        'detected_issues': None,
      }

    run = runs[0]
    run_id = run.info.run_id

    # Get markdown report
    try:
      markdown_path = f'analysis/experiment_summaries/{experiment_id}_summary.md'
      markdown_content = artifact_manager.download_analysis_report(run_id, markdown_path)
    except:
      markdown_content = None

    # Get structured data for schemas and issues
    schemas_with_label_types = None
    detected_issues = None
    metadata = {}

    try:
      data_path = f'analysis/experiment_summaries/{experiment_id}_analysis_data.json'
      json_content = artifact_manager.download_analysis_report(run_id, data_path)
      structured_data = json.loads(json_content)

      # Extract metadata
      metadata = structured_data.get('metadata', {})

      # Extract schemas with label types
      if 'raw_sme_analysis' in structured_data:
        sme_analysis = structured_data['raw_sme_analysis']

        if 'schema_recommendations' in sme_analysis:
          schemas = sme_analysis['schema_recommendations'].get('recommended_schemas', [])
          # Format schemas with label type information
          formatted_schemas = []
          for schema in schemas[:10]:  # Limit to top 10 schemas
            formatted_schemas.append(
              {
                'key': schema.get('key'),
                'name': schema.get('name'),
                'label_type': schema.get('label_type', 'NOT_SPECIFIED'),
                'schema_type': schema.get('schema_type'),
                'description': schema.get('description'),
                'rationale': schema.get('rationale'),
                'priority_score': schema.get('priority_score', 0),
                'grounded_in_traces': schema.get('grounded_in_traces', [])[
                  :3
                ],  # Limit trace examples
              }
            )
          schemas_with_label_types = formatted_schemas

        # Extract detected issues
        if 'issue_detection' in sme_analysis:
          issues = sme_analysis['issue_detection'].get('detected_issues', [])
          # Format issues for UI
          formatted_issues = []
          for issue in issues[:5]:  # Limit to top 5 issues
            formatted_issues.append(
              {
                'issue_type': issue.get('issue_type'),
                'severity': issue.get('severity'),
                'title': issue.get('title'),
                'description': issue.get('description'),
                'affected_traces': issue.get('affected_traces', 0),
                'example_traces': issue.get('example_traces', [])[:3],
                'problem_snippets': issue.get('problem_snippets', [])[:2],
              }
            )
          detected_issues = formatted_issues
    except Exception as e:
      logger.warning(f'Could not retrieve structured data: {e}')

    return {
      'has_summary': True,
      'content': markdown_content,
      'source': 'mlflow_artifacts',
      'run_id': run_id,
      'message': None,
      'schemas_with_label_types': schemas_with_label_types,
      'detected_issues': detected_issues,
      'metadata': {
        'analysis_timestamp': run.data.tags.get('analysis.experiment_summary.timestamp'),
        'model_endpoint': metadata.get('model_endpoint', 'unknown'),
        'traces_analyzed': metadata.get('traces_analyzed', metadata.get('total_traces_analyzed', 0)),
      },
    }

  except Exception as e:
    logger.error(f'Error retrieving experiment summary: {e}')
    # Fallback to local file system
    project_root = Path(__file__).parent.parent.parent.parent
    reports_dir = project_root / 'reports' / 'experiments'
    summary_file = reports_dir / f'{experiment_id}_summary.md'

    if summary_file.exists():
      try:
        with open(summary_file, 'r', encoding='utf-8') as f:
          content = f.read()
        return {
          'has_summary': True,
          'content': content,
          'source': 'local_file',
          'message': 'Summary from local file (MLflow retrieval failed).',
        }
      except:
        pass

    return {
      'has_summary': False,
      'content': None,
      'message': f'Error retrieving summary: {str(e)}',
    }


async def run_analysis_task(
  experiment_id: str, focus: str, trace_sample_size: int, model_endpoint: str
):
  """Background task to run AI analysis."""
  try:
    # Update status to running
    analysis_status_store[experiment_id] = AnalysisStatus(
      experiment_id=experiment_id, status='running', message='Analysis in progress...'
    )

    # Run the analysis
    analyzer = AIExperimentAnalyzer(model_endpoint)
    result = await analyzer.analyze_experiment(experiment_id, focus, trace_sample_size)

    # Store the analysis
    if result.get('status') == 'success':
      # The analyzer already stores to MLflow, just update status
      analysis_status_store[experiment_id] = AnalysisStatus(
        experiment_id=experiment_id,
        status='completed',
        message='Analysis completed successfully',
        run_id=result.get('metadata', {}).get('run_id'),
      )
    else:
      analysis_status_store[experiment_id] = AnalysisStatus(
        experiment_id=experiment_id, status='failed', message=result.get('error', 'Analysis failed')
      )

  except Exception as e:
    logger.error(f'Analysis task failed: {e}')
    analysis_status_store[experiment_id] = AnalysisStatus(
      experiment_id=experiment_id, status='failed', message=str(e)
    )


@router.post('/trigger-analysis', response_model=AnalysisStatus)
async def trigger_analysis(
  request: TriggerAnalysisRequest, background_tasks: BackgroundTasks
) -> AnalysisStatus:
  """Trigger AI analysis for an experiment.

  This runs the analysis in the background and returns immediately.

  Args:
      request: Analysis request parameters

  Returns:
      Status of the analysis request
  """
  try:
    # Check if analysis is already running
    if request.experiment_id in analysis_status_store:
      existing_status = analysis_status_store[request.experiment_id]
      if existing_status.status == 'running':
        return existing_status

    # Initialize status
    analysis_status_store[request.experiment_id] = AnalysisStatus(
      experiment_id=request.experiment_id, status='pending', message='Analysis queued'
    )

    # Add background task
    background_tasks.add_task(
      run_analysis_task,
      request.experiment_id,
      request.focus,
      request.trace_sample_size,
      request.model_endpoint,
    )

    return analysis_status_store[request.experiment_id]

  except Exception as e:
    logger.error(f'Error triggering analysis: {e}')
    raise HTTPException(status_code=500, detail=str(e))


@router.get('/status/{experiment_id}', response_model=AnalysisStatus)
async def get_analysis_status(experiment_id: str) -> AnalysisStatus:
  """Get the status of an analysis request.

  Args:
      experiment_id: The experiment ID

  Returns:
      Current status of the analysis
  """
  if experiment_id not in analysis_status_store:
    return AnalysisStatus(
      experiment_id=experiment_id,
      status='not_found',
      message='No analysis request found for this experiment',
    )

  return analysis_status_store[experiment_id]
