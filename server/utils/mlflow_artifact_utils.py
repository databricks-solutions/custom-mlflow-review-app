"""MLflow Artifact Utilities for Analysis Storage

This module provides utilities for storing and retrieving analysis reports
as MLflow artifacts instead of local file system storage.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class MLflowArtifactManager:
  """Manages MLflow artifacts for analysis reports and summaries."""

  def __init__(self):
    """Initialize the MLflow artifact manager."""
    self.client = MlflowClient()
    self.logger = logging.getLogger(__name__)

  def get_or_create_analysis_run(
    self,
    experiment_id: str = None,
    labeling_session_run_id: str = None,
    analysis_type: str = 'experiment_summary',
    description: str = None,
    tags: Dict[str, str] = None,
  ) -> str:
    """Get existing run or create metadata run for storing analysis artifacts.

    For labeling sessions: Uses the existing labeling session run ID
    For experiments: Uses or creates an experiment-level metadata run

    Args:
        experiment_id: The experiment ID (required if no labeling_session_run_id)
        labeling_session_run_id: Existing labeling session run ID to use
        analysis_type: Type of analysis (e.g., 'experiment_summary', 'session_analysis')
        description: Optional description of the analysis
        tags: Optional additional tags for the run

    Returns:
        The run ID to use for storing artifacts
    """
    try:
      # If labeling session run ID provided, use it directly
      if labeling_session_run_id:
        self.logger.info(
          f'Using existing labeling session run {labeling_session_run_id} for analysis storage'
        )
        # Add analysis tags to the existing run
        if tags or description:
          with mlflow.start_run(run_id=labeling_session_run_id):
            if description:
              mlflow.set_tag('analysis.description', description)
            if tags:
              for key, value in tags.items():
                mlflow.set_tag(key, value)
            mlflow.set_tag('analysis.timestamp', datetime.now().isoformat())
            mlflow.set_tag('analysis.type', analysis_type)
        return labeling_session_run_id

      # For experiments, look for existing metadata run or create one
      if experiment_id:
        # Search for existing experiment metadata run
        filter_string = f"tags.`mlflow.runName` = 'experiment_metadata' AND tags.`experiment.id` = '{experiment_id}'"
        existing_runs = self.client.search_runs(
          experiment_ids=[experiment_id], filter_string=filter_string, max_results=1
        )

        if existing_runs:
          # Use existing metadata run
          metadata_run_id = existing_runs[0].info.run_id
          self.logger.info(f'Using existing experiment metadata run {metadata_run_id}')

          # Update tags for this analysis
          with mlflow.start_run(run_id=metadata_run_id):
            mlflow.set_tag(f'analysis.{analysis_type}.timestamp', datetime.now().isoformat())
            if description:
              mlflow.set_tag(f'analysis.{analysis_type}.description', description)
            if tags:
              for key, value in tags.items():
                mlflow.set_tag(key, value)

          return metadata_run_id
        else:
          # Create new experiment metadata run
          run_tags = {
            'mlflow.runName': 'experiment_metadata',
            'experiment.id': experiment_id,
            'metadata.type': 'experiment_analysis',
            'created.timestamp': datetime.now().isoformat(),
            f'analysis.{analysis_type}.timestamp': datetime.now().isoformat(),
          }

          if description:
            run_tags[f'analysis.{analysis_type}.description'] = description

          if tags:
            run_tags.update(tags)

          # Create the metadata run
          run = self.client.create_run(experiment_id=experiment_id, tags=run_tags)

          self.logger.info(f'Created experiment metadata run {run.info.run_id}')
          return run.info.run_id

      raise ValueError('Either experiment_id or labeling_session_run_id must be provided')

    except Exception as e:
      self.logger.error(f'Error getting/creating analysis run: {e}')
      raise

  def log_analysis_report(
    self,
    run_id: str,
    content: str,
    report_name: str,
    report_type: str = 'markdown',
    artifact_path: str = None,
  ) -> str:
    """Log an analysis report as an MLflow artifact.

    Args:
        run_id: The MLflow run ID to log the artifact to
        content: The content of the report
        report_name: Name of the report file (without extension)
        report_type: Type of report ('markdown', 'json', 'yaml', 'text')
        artifact_path: Optional subdirectory path within artifacts

    Returns:
        The artifact path where the report was stored
    """
    try:
      # Determine file extension based on report type
      extensions = {'markdown': '.md', 'json': '.json', 'yaml': '.yaml', 'text': '.txt'}
      extension = extensions.get(report_type, '.txt')

      # Construct full artifact file path
      if artifact_path:
        full_artifact_path = f'{artifact_path}/{report_name}{extension}'
      else:
        full_artifact_path = f'{report_name}{extension}'

      # Use mlflow context manager to log to specific run
      with mlflow.start_run(run_id=run_id):
        # Log the content as text artifact
        mlflow.log_text(content, full_artifact_path)

        # Log additional metadata about the report
        report_metadata = {
          'report_name': report_name,
          'report_type': report_type,
          'content_length': len(content),
          'created_at': datetime.now().isoformat(),
          'artifact_path': full_artifact_path,
        }

        # Log metadata as JSON
        metadata_path = f'{artifact_path}/metadata.json' if artifact_path else 'metadata.json'
        mlflow.log_dict(report_metadata, metadata_path)

      self.logger.info(
        f'Logged analysis report {report_name} to run {run_id} at {full_artifact_path}'
      )
      return full_artifact_path

    except Exception as e:
      self.logger.error(f'Error logging analysis report: {e}')
      raise

  def log_structured_analysis(
    self, run_id: str, analysis_data: Dict[str, Any], analysis_name: str, artifact_path: str = None
  ) -> str:
    """Log structured analysis data as JSON artifact.

    Args:
        run_id: The MLflow run ID to log the artifact to
        analysis_data: Dictionary containing analysis data
        analysis_name: Name for the analysis artifact
        artifact_path: Optional subdirectory path within artifacts

    Returns:
        The artifact path where the data was stored
    """
    try:
      # Construct artifact path
      if artifact_path:
        full_artifact_path = f'{artifact_path}/{analysis_name}.json'
      else:
        full_artifact_path = f'{analysis_name}.json'

      # Use mlflow context manager to log to specific run
      with mlflow.start_run(run_id=run_id):
        # Log the structured data
        mlflow.log_dict(analysis_data, full_artifact_path)

      self.logger.info(f'Logged structured analysis {analysis_name} to run {run_id}')
      return full_artifact_path

    except Exception as e:
      self.logger.error(f'Error logging structured analysis: {e}')
      raise

  def list_analysis_artifacts(self, run_id: str, path: str = None) -> List[Dict[str, Any]]:
    """List all artifacts in an analysis run.

    Args:
        run_id: The MLflow run ID to list artifacts from
        path: Optional path within artifacts to list (None for root)

    Returns:
        List of artifact info dictionaries
    """
    try:
      artifacts = self.client.list_artifacts(run_id, path=path)

      artifact_list = []
      for artifact in artifacts:
        artifact_info = {
          'path': artifact.path,
          'is_dir': artifact.is_dir,
          'file_size': artifact.file_size if hasattr(artifact, 'file_size') else None,
        }
        artifact_list.append(artifact_info)

      return artifact_list

    except Exception as e:
      self.logger.error(f'Error listing artifacts: {e}')
      raise

  def download_analysis_report(self, run_id: str, artifact_path: str) -> str:
    """Download and return the content of an analysis report.

    Args:
        run_id: The MLflow run ID containing the artifact
        artifact_path: Path to the artifact within the run

    Returns:
        The content of the report as a string
    """
    try:
      # Download artifact to temporary directory
      with tempfile.TemporaryDirectory() as temp_dir:
        # Download the specific artifact
        downloaded_path = self.client.download_artifacts(
          run_id=run_id, path=artifact_path, dst_path=temp_dir
        )

        # Read and return the content
        file_path = Path(downloaded_path)
        if file_path.is_file():
          with open(file_path, 'r') as f:
            content = f.read()
          return content
        else:
          raise ValueError(f'Downloaded artifact {artifact_path} is not a file')

    except Exception as e:
      self.logger.error(f'Error downloading analysis report: {e}')
      raise

  def get_analysis_artifact_uri(self, run_id: str, artifact_path: str = None) -> str:
    """Get the URI for accessing an artifact.

    Args:
        run_id: The MLflow run ID containing the artifact
        artifact_path: Optional specific path within artifacts

    Returns:
        The artifact URI
    """
    try:
      run = self.client.get_run(run_id)
      base_uri = run.info.artifact_uri

      if artifact_path:
        return f'{base_uri}/{artifact_path}'
      else:
        return base_uri

    except Exception as e:
      self.logger.error(f'Error getting artifact URI: {e}')
      raise

  def list_analysis_runs(
    self, experiment_id: str, analysis_type: str = None, max_results: int = 100
  ) -> List[Dict[str, Any]]:
    """List all analysis runs in an experiment.

    Args:
        experiment_id: The experiment ID to search in
        analysis_type: Optional filter by analysis type
        max_results: Maximum number of runs to return

    Returns:
        List of analysis run information
    """
    try:
      # Build filter string for analysis runs
      filter_conditions = ["tags.`analysis.type` LIKE '%'"]

      if analysis_type:
        filter_conditions = [f"tags.`analysis.type` = '{analysis_type}'"]

      filter_string = ' AND '.join(filter_conditions)

      # Search for runs
      runs = self.client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=filter_string,
        max_results=max_results,
        order_by=['start_time DESC'],
      )

      run_list = []
      for run in runs:
        run_info = {
          'run_id': run.info.run_id,
          'run_name': run.data.tags.get('mlflow.runName', 'Unnamed'),
          'analysis_type': run.data.tags.get('analysis.type', 'unknown'),
          'timestamp': run.data.tags.get('analysis.timestamp'),
          'description': run.data.tags.get('mlflow.note.content', ''),
          'start_time': run.info.start_time,
          'artifact_uri': run.info.artifact_uri,
          'status': run.info.status,
        }
        run_list.append(run_info)

      return run_list

    except Exception as e:
      self.logger.error(f'Error listing analysis runs: {e}')
      raise

  def store_experiment_summary(
    self,
    experiment_id: str,
    summary_content: str,
    summary_data: Dict[str, Any],
    labeling_session_run_id: str = None,
    tags: Dict[str, str] = None,
  ) -> Dict[str, str]:
    """Store a comprehensive experiment summary as MLflow artifacts.

    Args:
        experiment_id: The experiment ID to store summary for
        summary_content: Markdown content of the summary
        summary_data: Structured data from the analysis
        labeling_session_run_id: Optional labeling session run ID to use
        tags: Optional additional tags for the run

    Returns:
        Dictionary with run_id and artifact paths
    """
    try:
      # Get or create appropriate run for storing artifacts
      run_id = self.get_or_create_analysis_run(
        experiment_id=experiment_id,
        labeling_session_run_id=labeling_session_run_id,
        analysis_type='experiment_summary' if not labeling_session_run_id else 'session_analysis',
        description='Comprehensive SME engagement analysis',
        tags=tags,
      )

      # Store markdown summary
      summary_path = self.log_analysis_report(
        run_id=run_id,
        content=summary_content,
        report_name=f'{experiment_id}_summary',
        report_type='markdown',
        artifact_path='analysis/experiment_summaries',
      )

      # Store structured data
      data_path = self.log_structured_analysis(
        run_id=run_id,
        analysis_data=summary_data,
        analysis_name=f'{experiment_id}_analysis_data',
        artifact_path='analysis/experiment_summaries',
      )

      # Log summary metrics as MLflow metrics for easy querying
      with mlflow.start_run(run_id=run_id):
        if 'executive_summary' in summary_data:
          exec_summary = summary_data['executive_summary']
          mlflow.log_metric('total_traces_analyzed', exec_summary.get('total_traces_analyzed', 0))
          mlflow.log_metric('critical_issues_found', exec_summary.get('critical_issues_found', 0))
          mlflow.log_metric('recommended_schemas', exec_summary.get('recommended_schemas', 0))
          mlflow.log_metric('suggested_sessions', exec_summary.get('suggested_sessions', 0))

      return {
        'run_id': run_id,
        'summary_path': summary_path,
        'data_path': data_path,
        'artifact_uri': self.get_analysis_artifact_uri(run_id),
      }

    except Exception as e:
      self.logger.error(f'Error storing experiment summary: {e}')
      raise


# Convenience functions for direct usage


def store_analysis_as_artifact(
  experiment_id: str = None,
  content: str = None,
  analysis_type: str = 'experiment_summary',
  metadata: Dict[str, Any] = None,
  labeling_session_run_id: str = None,
) -> Dict[str, str]:
  """Convenience function to store analysis content as MLflow artifact.

  Args:
      experiment_id: The experiment ID to associate with (required if no labeling_session_run_id)
      content: The analysis content (markdown or text)
      analysis_type: Type of analysis being stored
      metadata: Optional metadata to store alongside
      labeling_session_run_id: Optional labeling session run ID to use instead

  Returns:
      Dictionary with storage details
  """
  manager = MLflowArtifactManager()

  # Get or create appropriate run for this analysis
  run_id = manager.get_or_create_analysis_run(
    experiment_id=experiment_id,
    labeling_session_run_id=labeling_session_run_id,
    analysis_type=analysis_type,
  )

  # Store the content
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  artifact_path = manager.log_analysis_report(
    run_id=run_id,
    content=content,
    report_name=f'{experiment_id}_{analysis_type}_{timestamp}',
    report_type='markdown',
    artifact_path=f'analysis/{analysis_type}',
  )

  # Store metadata if provided
  if metadata:
    manager.log_structured_analysis(
      run_id=run_id,
      analysis_data=metadata,
      analysis_name='analysis_metadata',
      artifact_path=f'analysis/{analysis_type}',
    )

  return {
    'run_id': run_id,
    'artifact_path': artifact_path,
    'artifact_uri': manager.get_analysis_artifact_uri(run_id, artifact_path),
  }


def retrieve_latest_analysis(
  experiment_id: str, analysis_type: str = 'experiment_summary'
) -> Optional[str]:
  """Retrieve the latest analysis of a given type for an experiment.

  Args:
      experiment_id: The experiment ID to search
      analysis_type: Type of analysis to retrieve

  Returns:
      The content of the latest analysis, or None if not found
  """
  manager = MLflowArtifactManager()

  # Find the latest analysis run
  runs = manager.list_analysis_runs(
    experiment_id=experiment_id, analysis_type=analysis_type, max_results=1
  )

  if not runs:
    return None

  latest_run = runs[0]
  run_id = latest_run['run_id']

  # List artifacts to find the summary
  artifacts = manager.list_analysis_artifacts(run_id)

  # Find the markdown summary file
  for artifact in artifacts:
    if artifact['path'].endswith('.md') and 'summary' in artifact['path']:
      return manager.download_analysis_report(run_id, artifact['path'])

  return None
