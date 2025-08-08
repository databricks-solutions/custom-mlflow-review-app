"""MLflow utility functions for direct use as tools by Claude."""

import inspect
import json
import logging
import time
from typing import Any, Dict, List, Optional

import mlflow
from mlflow.entities import AssessmentSource

from server.utils.config import get_config
from server.utils.databricks_auth import get_mlflow_api_url
from server.utils.proxy import fetch_databricks_sync

# Global initialization flag
_initialized = False


def _ensure_mlflow_initialized():
  """Ensure MLflow is initialized globally (lazy loading)."""
  global _initialized
  if _initialized:
    return

  logger = logging.getLogger(__name__)
  start_time = time.time()

  logger.info('🔧 [MLFLOW UTILS] Initializing MLflow...')

  # Set default experiment context from config
  try:
    config = get_config()
    experiment_id = config.get('experiment_id')
    if experiment_id:
      mlflow.set_experiment(experiment_id=experiment_id)
  except Exception:
    # Don't fail initialization if config is unavailable
    pass

  _initialized = True
  init_time = time.time() - start_time
  logger.info(f'✅ [MLFLOW UTILS] MLflow initialized in {init_time * 1000:.1f}ms')


def _extract_request_response_preview(trace) -> tuple[Optional[str], Optional[str]]:
  """Extract request and response previews from trace data.

  Returns:
      Tuple of (request_preview, response_preview)
  """

  def truncate(text: str, length: int = 200) -> str:
    """Truncate text to specified length."""
    return text[:length] + '...' if len(text) > length else text

  def extract_user_message(messages: list) -> Optional[str]:
    """Extract last user message from messages list."""
    for msg in reversed(messages):
      if isinstance(msg, dict):
        # Check both 'role' and 'type' fields for user messages
        if msg.get('role') == 'user' or msg.get('type') == 'human':
          content = msg.get('content', '')
          if content:
            return truncate(content)
    return None

  def parse_json_safely(data) -> Any:
    """Safely parse JSON string or return data as-is."""
    if isinstance(data, str):
      try:
        return json.loads(data)
      except json.JSONDecodeError:
        return None
    return data

  request_preview = None
  response_preview = None

  try:
    # 1. Check trace metadata first (most reliable source)
    if hasattr(trace.info, 'request_metadata') and trace.info.request_metadata:
      metadata = trace.info.request_metadata

      # Extract request from traceInputs
      trace_inputs = parse_json_safely(metadata.get('mlflow.traceInputs'))
      if isinstance(trace_inputs, dict) and 'messages' in trace_inputs:
        request_preview = extract_user_message(trace_inputs['messages'])

      # Extract response from traceOutputs (skip if truncated)
      trace_outputs = metadata.get('mlflow.traceOutputs', '')
      if not (isinstance(trace_outputs, str) and trace_outputs.endswith('...')):
        outputs = parse_json_safely(trace_outputs)
        if isinstance(outputs, dict):
          # Try choices format
          if 'choices' in outputs and outputs['choices']:
            choice = outputs['choices'][0]
            if isinstance(choice, dict) and 'message' in choice:
              content = choice['message'].get('content', '')
              if content:
                response_preview = truncate(content)
          # Try direct text format
          elif 'text' in outputs:
            response_preview = truncate(str(outputs['text']))

    # 2. If we have both previews, we're done
    if request_preview and response_preview:
      return request_preview, response_preview

    # 3. Check spans as fallback
    if trace.data and trace.data.spans:
      for span in trace.data.spans:
        attributes = getattr(span, 'attributes', {})
        span_type = attributes.get('mlflow.spanType', '')

        if span_type in ['CHAT_MODEL', 'AGENT']:
          # Extract request if not found yet
          if not request_preview:
            span_inputs = parse_json_safely(attributes.get('mlflow.spanInputs'))
            if span_inputs:
              if isinstance(span_inputs, dict) and 'messages' in span_inputs:
                request_preview = extract_user_message(span_inputs['messages'])
              elif isinstance(span_inputs, list) and span_inputs:
                # Handle list format
                messages = span_inputs[0] if isinstance(span_inputs[0], list) else span_inputs
                request_preview = extract_user_message(messages)

          # Extract response if not found yet
          if not response_preview:
            span_outputs = parse_json_safely(attributes.get('mlflow.spanOutputs'))
            if isinstance(span_outputs, dict):
              # Try choices format
              if 'choices' in span_outputs and span_outputs['choices']:
                choice = span_outputs['choices'][0]
                if isinstance(choice, dict) and 'message' in choice:
                  content = choice['message'].get('content', '')
                  if content:
                    response_preview = truncate(content)
              # Try generations format
              elif 'generations' in span_outputs and span_outputs['generations']:
                gen = span_outputs['generations'][0]
                if isinstance(gen, list) and gen:
                  text = gen[0].get('text', '') or gen[0].get('message', {}).get('content', '')
                  if text:
                    response_preview = truncate(text)
              # Try direct text
              elif 'text' in span_outputs:
                response_preview = truncate(str(span_outputs['text']))

          # Stop if we found both
          if request_preview and response_preview:
            break

  except Exception as e:
    logger = logging.getLogger(__name__)
    logger.debug(f'Failed to extract previews for trace: {str(e)}')

  return request_preview, response_preview


def search_traces(
  experiment_ids: Optional[List[str]] = None,
  filter_string: Optional[str] = None,
  run_id: Optional[str] = None,
  max_results: Optional[int] = 1000,
  order_by: Optional[List[str]] = None,
):
  """Search for traces in MLflow experiments.

  Simple wrapper around mlflow.search_traces() that returns raw MLflow Trace objects.

  Args:
      experiment_ids: Optional list of experiment IDs to search in
      filter_string: Optional filter string for traces (SQL-like DSL)
      run_id: Optional run ID to filter by
      max_results: Maximum number of results to return
      order_by: Optional list of fields to order by

  Returns:
      List of MLflow Trace objects (or empty list if no traces found)
  """
  _ensure_mlflow_initialized()

  logger = logging.getLogger(__name__)
  start_time = time.time()

  # Get caller information for debugging
  frame = inspect.currentframe()
  caller_info = 'unknown'
  if frame and frame.f_back:
    caller_frame = frame.f_back
    caller_module = caller_frame.f_globals.get('__name__', 'unknown')
    caller_function = caller_frame.f_code.co_name
    caller_line = caller_frame.f_lineno
    caller_info = f'{caller_module}:{caller_function}:{caller_line}'

  logger.info(
    f'🔍 [MLFLOW SDK] search_traces called from: {caller_info} | experiments: {experiment_ids}, max_results: {max_results}, filter: {filter_string}, run_id: {run_id}'
  )

  try:
    # If searching by run_id without experiment_ids, get the experiment from the run
    if run_id and not experiment_ids:
      try:
        run = mlflow.get_run(run_id)
        experiment_ids = [run.info.experiment_id]
        logger.info(f'🔍 [MLFLOW UTILS] Got experiment_id {experiment_ids[0]} from run {run_id}')
      except Exception as e:
        logger.warning(f'⚠️ [MLFLOW UTILS] Could not get experiment from run {run_id}: {str(e)}')
        experiment_ids = None

    # Call MLflow SDK directly and return raw Trace objects
    traces = mlflow.search_traces(
      experiment_ids=experiment_ids,
      filter_string=filter_string,
      run_id=run_id,
      max_results=max_results or 1000,
      order_by=order_by,
      return_type='list',  # Return list of Trace objects
    )

    # Handle case where search_traces returns None
    if traces is None:
      traces = []

    total_time = time.time() - start_time
    logger.info(
      f'✅ [MLFLOW UTILS] search_traces completed in {total_time * 1000:.1f}ms, returned {len(traces)} traces'
    )

    return traces

  except Exception as e:
    error_time = time.time() - start_time
    logger.error(
      f'❌ [MLFLOW UTILS] search_traces failed after {error_time * 1000:.1f}ms: {str(e)}'
    )
    raise Exception(f'Failed to search traces: {str(e)}')


def get_experiment(experiment_id: str):
  """Get experiment details by ID.

  Args:
      experiment_id: The experiment ID

  Returns:
      MLflow Experiment object with REST API compatible structure
  """
  _ensure_mlflow_initialized()

  logger = logging.getLogger(__name__)
  start_time = time.time()
  logger.info(f'🔍 [MLFLOW UTILS] Starting get_experiment for {experiment_id}')

  try:
    experiment = mlflow.get_experiment(experiment_id)

    total_time = time.time() - start_time
    logger.info(
      f'✅ [MLFLOW UTILS] get_experiment completed in {total_time * 1000:.1f}ms for {experiment_id}'
    )

    # Return minimal wrapper for API compatibility
    # MLflow Experiment object has fields with underscores, need to map them
    return {
      'experiment': {
        'experiment_id': experiment.experiment_id,
        'name': experiment.name,
        'artifact_location': experiment.artifact_location,
        'lifecycle_stage': experiment.lifecycle_stage,
        'creation_time': experiment.creation_time,
        'last_update_time': experiment.last_update_time,
      }
    }

  except Exception as e:
    error_time = time.time() - start_time
    logger.error(
      f'❌ [MLFLOW UTILS] get_experiment failed after {error_time * 1000:.1f}ms for {experiment_id}: {str(e)}'
    )
    raise


def _serialize_run_io(run_io_obj):
  """Safely serialize MLflow RunInputs/RunOutputs objects.
  
  Args:
      run_io_obj: MLflow RunInputs or RunOutputs object or None
      
  Returns:
      Serializable dictionary or empty dict if None/error
  """
  if run_io_obj is None:
    return {}
    
  try:
    # Try to convert to dict if it has a to_dict method
    if hasattr(run_io_obj, 'to_dict'):
      return run_io_obj.to_dict()
    
    # Try to access common attributes for RunInputs/RunOutputs
    result = {}
    
    # For RunInputs
    if hasattr(run_io_obj, 'dataset_inputs'):
      try:
        dataset_inputs = []
        for dataset_input in run_io_obj.dataset_inputs:
          if hasattr(dataset_input, 'to_dict'):
            dataset_inputs.append(dataset_input.to_dict())
          else:
            # Manually extract common attributes
            dataset_inputs.append({
              'dataset': getattr(dataset_input, 'dataset', {}),
              'tags': getattr(dataset_input, 'tags', []),
            })
        result['dataset_inputs'] = dataset_inputs
      except Exception as e:
        logging.getLogger(__name__).warning(f'⚠️ Could not serialize dataset_inputs: {str(e)}')
        result['dataset_inputs'] = []
    
    # Add any other attributes that might be present
    for attr_name in ['tags', 'metadata', 'properties']:
      if hasattr(run_io_obj, attr_name):
        try:
          attr_value = getattr(run_io_obj, attr_name)
          if isinstance(attr_value, (dict, list, str, int, float, bool)) or attr_value is None:
            result[attr_name] = attr_value
          else:
            # Try to convert to dict or skip
            if hasattr(attr_value, 'to_dict'):
              result[attr_name] = attr_value.to_dict()
            elif hasattr(attr_value, '__dict__'):
              result[attr_name] = attr_value.__dict__
            else:
              result[attr_name] = str(attr_value)
        except Exception as e:
          logging.getLogger(__name__).warning(f'⚠️ Could not serialize {attr_name}: {str(e)}')
          
    return result
    
  except Exception as e:
    logging.getLogger(__name__).warning(f'⚠️ Could not serialize run I/O object: {str(e)}')
    return {}


def get_run(run_id: str):
  """Get run details by ID.

  Args:
      run_id: The run ID

  Returns:
      MLflow Run object with REST API compatible structure
  """
  _ensure_mlflow_initialized()

  logger = logging.getLogger(__name__)
  logger.info(f'🔍 [MLFLOW UTILS] Starting get_run for {run_id}')

  try:
    run = mlflow.get_run(run_id)
    logger.info(f'✅ [MLFLOW UTILS] Successfully retrieved run {run_id}')

    # Safely extract run name with fallback chain
    run_name = ''
    try:
      # Try direct attribute first
      run_name = getattr(run.info, 'run_name', '')
      if not run_name and run.data and run.data.tags:
        # Fallback to mlflow.runName tag
        run_name = run.data.tags.get('mlflow.runName', '')
      logger.info(f'📝 [MLFLOW UTILS] Run name extracted: "{run_name}"')
    except Exception as e:
      logger.warning(f'⚠️ [MLFLOW UTILS] Could not extract run name: {str(e)}')
      run_name = ''

    # Safely extract metrics
    metrics = []
    try:
      if run.data and run.data.metrics:
        metrics = [
          {'key': k, 'value': v.value, 'timestamp': v.timestamp, 'step': v.step}
          for k, v in run.data.metrics.items()
        ]
      logger.info(f'📊 [MLFLOW UTILS] Extracted {len(metrics)} metrics')
    except Exception as e:
      logger.warning(f'⚠️ [MLFLOW UTILS] Could not extract metrics: {str(e)}')
      metrics = []

    # Safely extract params
    params = []
    try:
      if run.data and run.data.params:
        params = [{'key': k, 'value': v} for k, v in run.data.params.items()]
      logger.info(f'⚙️ [MLFLOW UTILS] Extracted {len(params)} params')
    except Exception as e:
      logger.warning(f'⚠️ [MLFLOW UTILS] Could not extract params: {str(e)}')
      params = []

    # Safely extract tags
    tags = []
    try:
      if run.data and run.data.tags:
        tags = [{'key': k, 'value': v} for k, v in run.data.tags.items()]
      logger.info(f'🏷️ [MLFLOW UTILS] Extracted {len(tags)} tags')
    except Exception as e:
      logger.warning(f'⚠️ [MLFLOW UTILS] Could not extract tags: {str(e)}')
      tags = []

    # Return run object with minimal wrapper for API compatibility
    result = {
      'run': {
        'info': {
          'run_id': run.info.run_id,
          'run_uuid': run.info.run_id,
          'experiment_id': run.info.experiment_id,
          'run_name': run_name,
          'status': run.info.status,
          'start_time': run.info.start_time,
          'end_time': getattr(run.info, 'end_time', None),
          'artifact_uri': run.info.artifact_uri,
          'lifecycle_stage': run.info.lifecycle_stage,
        },
        'data': {
          'metrics': metrics,
          'params': params,
          'tags': tags,
        },
        'inputs': _serialize_run_io(getattr(run, 'inputs', None)),
        'outputs': _serialize_run_io(getattr(run, 'outputs', None)),
      }
    }
    
    logger.info(f'✅ [MLFLOW UTILS] Successfully formatted run {run_id} response')
    return result

  except Exception as e:
    logger.error(f'❌ [MLFLOW UTILS] get_run failed for {run_id}: {str(e)}')
    logger.exception(f'Full traceback for run {run_id}:')
    raise Exception(f'Failed to get run {run_id}: {str(e)}')


def create_run(data: Dict[str, Any]):
  """Create a new MLflow run.

  Args:
      data: Run creation data

  Returns:
      Created run details
  """
  _ensure_mlflow_initialized()

  experiment_id = data.get('experiment_id')
  run_name = data.get('run_name')
  tags = data.get('tags', {})

  if run_name:
    tags['mlflow.runName'] = run_name

  with mlflow.start_run(experiment_id=experiment_id, run_name=run_name, tags=tags) as run:
    run_id = run.info.run_id

  return get_run(run_id)


def update_run(data: Dict[str, Any]):
  """Update an MLflow run.

  Args:
      data: Run update data

  Returns:
      Success message
  """
  _ensure_mlflow_initialized()

  run_id = data.get('run_id')
  status = data.get('status')
  end_time = data.get('end_time')

  client = mlflow.MlflowClient()

  if status:
    client.set_terminated(run_id, status, end_time)

  if 'tags' in data:
    for tag in data['tags']:
      client.set_tag(run_id, tag['key'], tag['value'])

  return {'message': 'Run updated successfully'}


def search_runs(data: Dict[str, Any]):
  """Search for runs in experiments.

  Args:
      data: Search parameters

  Returns:
      Search results with runs
  """
  _ensure_mlflow_initialized()

  experiment_ids = data.get('experiment_ids', [])
  filter_string = data.get('filter', '')
  max_results = data.get('max_results', 1000)
  order_by = data.get('order_by', [])
  page_token = data.get('page_token')

  runs_df = mlflow.search_runs(
    experiment_ids=experiment_ids,
    filter_string=filter_string,
    max_results=max_results,
    order_by=order_by,
    page_token=page_token,
  )

  # Convert DataFrame to list of run dicts
  runs = runs_df.to_dict('records') if not runs_df.empty else []

  # Transform to match expected API format
  formatted_runs = []
  for run in runs:
    formatted_runs.append(
      {
        'info': {
          'run_id': run.get('run_id'),
          'experiment_id': run.get('experiment_id'),
          'status': run.get('status'),
          'start_time': run.get('start_time'),
          'end_time': run.get('end_time'),
          'artifact_uri': run.get('artifact_uri'),
          'lifecycle_stage': run.get('lifecycle_stage'),
        },
        'data': {
          'tags': [
            {'key': k.replace('tags.', ''), 'value': v}
            for k, v in run.items()
            if k.startswith('tags.')
          ],
        },
      }
    )

  return {'runs': formatted_runs, 'next_page_token': None}


def link_traces_to_run(run_id: str, trace_ids: List[str]) -> Dict[str, Any]:
  """Link traces to an MLflow run.

  Args:
      run_id: The MLflow run ID to link traces to
      trace_ids: List of trace IDs to link

  Returns:
      Dictionary containing link operation result
  """
  _ensure_mlflow_initialized()

  url = get_mlflow_api_url('/traces/link-to-run')
  data = {'run_id': run_id, 'trace_ids': trace_ids}
  return fetch_databricks_sync(method='POST', url=url, data=data)


def get_trace(trace_id: str):
  """Get trace information by ID.

  Simple wrapper around mlflow.get_trace() that returns raw MLflow Trace objects.

  Args:
      trace_id: The trace ID

  Returns:
      MLflow Trace object
  """
  _ensure_mlflow_initialized()

  logger = logging.getLogger(__name__)
  start_time = time.time()

  # Get caller information for debugging
  frame = inspect.currentframe()
  caller_info = 'unknown'
  if frame and frame.f_back:
    caller_frame = frame.f_back
    caller_module = caller_frame.f_globals.get('__name__', 'unknown')
    caller_function = caller_frame.f_code.co_name
    caller_line = caller_frame.f_lineno
    caller_info = f'{caller_module}:{caller_function}:{caller_line}'

  logger.info(f'🔍 [MLFLOW SDK] get_trace called from: {caller_info} | trace_id: {trace_id}')

  try:
    # Call MLflow SDK directly and return raw Trace object
    trace = mlflow.get_trace(trace_id)

    total_time = time.time() - start_time
    logger.info(
      f'✅ [MLFLOW UTILS] get_trace completed in {total_time * 1000:.1f}ms for {trace_id}'
    )

    return trace

  except Exception as e:
    error_time = time.time() - start_time
    logger.error(
      f'❌ [MLFLOW UTILS] get_trace failed after {error_time * 1000:.1f}ms for {trace_id}: {str(e)}'
    )
    raise Exception(f'Trace not found: {str(e)}')


def get_trace_data(trace_id: str) -> Dict[str, Any]:
  """Get trace data (spans) by trace ID.

  Args:
      trace_id: The trace ID

  Returns:
      Dictionary containing trace data
  """
  _ensure_mlflow_initialized()

  # Use MLflow SDK - get_trace already includes trace data
  trace = mlflow.get_trace(trace_id)

  # Return just the trace data (spans)
  return {
    'trace_data': {
      'spans': trace.data.spans if hasattr(trace.data, 'spans') else [],
      'request': trace.data.request if hasattr(trace.data, 'request') else None,
      'response': trace.data.response if hasattr(trace.data, 'response') else None,
    }
  }


def log_feedback(
  trace_id: str, key: str, value: Any, username: str, rationale: Optional[str] = None
) -> Dict[str, Any]:
  """Log feedback on a trace.

  Args:
      trace_id: The trace ID
      key: The feedback key
      value: The feedback value (can be str, int, float, bool, or dict)
      username: The username of the person providing feedback
      rationale: Optional rationale about the feedback

  Returns:
      Dictionary containing operation result
  """
  _ensure_mlflow_initialized()

  try:
    # Prepare metadata with rationale as workaround for MLflow bug
    metadata = {'rationale': rationale} if rationale else None
    
    # Log feedback using MLflow with user identity
    # Note: rationale parameter doesn't work in MLflow 3.1.1, using metadata instead
    assessment = mlflow.log_feedback(
      trace_id=trace_id,
      name=key,
      value=value,
      source=AssessmentSource(source_type='human', source_id=username),
      metadata=metadata,
    )

    return {
      'success': True,
      'message': f'Feedback logged successfully for trace {trace_id} by user {username}',
      'assessment_id': assessment.assessment_id if hasattr(assessment, 'assessment_id') else None,
    }
  except Exception as e:
    raise Exception(f'Failed to log feedback: {str(e)}')


def update_feedback(
  trace_id: str, assessment_id: str, value: Any, username: str, rationale: Optional[str] = None
) -> Dict[str, Any]:
  """Update existing feedback on a trace.

  Args:
      trace_id: The trace ID
      assessment_id: The assessment ID to update
      value: The feedback value (can be str, int, float, bool, or dict)
      username: The username of the person providing feedback
      rationale: Optional rationale about the feedback

  Returns:
      Dictionary containing operation result
  """
  _ensure_mlflow_initialized()

  try:
    # Prepare metadata with rationale as workaround for MLflow bug
    metadata = {'rationale': rationale} if rationale else None
    
    # Update feedback using MLflow with user identity
    assessment = mlflow.override_feedback(
      trace_id=trace_id,
      assessment_id=assessment_id,
      value=value,
      source=AssessmentSource(source_type='human', source_id=username),
      metadata=metadata,
      rationale=rationale,  # Try both - MLflow might fix this in future versions
    )

    return {
      'success': True,
      'message': f'Feedback updated successfully for trace {trace_id} by user {username}',
      'assessment_id': assessment.assessment_id if hasattr(assessment, 'assessment_id') else assessment_id,
    }
  except Exception as e:
    raise Exception(f'Failed to update feedback: {str(e)}')


def log_expectation(
  trace_id: str, key: str, value: Any, username: str, rationale: Optional[str] = None
) -> Dict[str, Any]:
  """Log expectation on a trace.

  Args:
      trace_id: The trace ID
      key: The expectation key
      value: The expectation value (can be str, int, float, bool, or dict)
      username: The username of the person providing expectation
      rationale: Optional rationale about the expectation

  Returns:
      Dictionary containing operation result
  """
  _ensure_mlflow_initialized()

  try:
    # Prepare metadata with rationale as workaround for MLflow bug
    metadata = {'rationale': rationale} if rationale else None
    
    # Log expectation using MLflow with user identity
    # Note: rationale parameter doesn't work in MLflow 3.1.1, using metadata instead
    assessment = mlflow.log_expectation(
      trace_id=trace_id,
      name=key,
      value=value,
      source=AssessmentSource(source_type='human', source_id=username),
      metadata=metadata,
    )

    return {
      'success': True,
      'message': f'Expectation logged successfully for trace {trace_id} by user {username}',
      'assessment_id': assessment.assessment_id if hasattr(assessment, 'assessment_id') else None,
    }
  except Exception as e:
    raise Exception(f'Failed to log expectation: {str(e)}')


def update_expectation(
  trace_id: str, assessment_id: str, value: Any, username: str, rationale: Optional[str] = None
) -> Dict[str, Any]:
  """Update existing expectation on a trace.

  Args:
      trace_id: The trace ID
      assessment_id: The assessment ID to update
      value: The expectation value (can be str, int, float, bool, or dict)
      username: The username of the person providing expectation
      rationale: Optional rationale about the expectation

  Returns:
      Dictionary containing operation result
  """
  _ensure_mlflow_initialized()

  try:
    # For expectations, we need to use update_assessment instead of override_feedback
    # First get the current assessment to preserve the name
    current = mlflow.get_assessment(trace_id=trace_id, assessment_id=assessment_id)
    
    # Create updated assessment
    from mlflow.entities import Assessment
    
    # Prepare metadata with rationale as workaround for MLflow bug
    metadata = {'rationale': rationale} if rationale else None
    
    updated_assessment = Assessment(
      name=current.name,
      value=value,
      source=AssessmentSource(source_type='human', source_id=username),
      metadata=metadata,
    )
    
    # Update the assessment
    assessment = mlflow.update_assessment(
      trace_id=trace_id,
      assessment_id=assessment_id,
      assessment=updated_assessment,
    )

    return {
      'success': True,
      'message': f'Expectation updated successfully for trace {trace_id} by user {username}',
      'assessment_id': assessment.assessment_id if hasattr(assessment, 'assessment_id') else assessment_id,
    }
  except Exception as e:
    raise Exception(f'Failed to update expectation: {str(e)}')
