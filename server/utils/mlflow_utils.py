"""MLflow utility functions for direct use as tools by Claude."""

from typing import Any, Dict, List, Optional

import mlflow
from mlflow.tracking import MlflowClient

from server.utils.databricks_auth import get_mlflow_api_url
from server.utils.proxy import fetch_databricks_sync


class MLflowUtils:
  """Utility class for MLflow operations that can be used directly by Claude."""

  def __init__(self):
    """Initialize MLflow client with Databricks tracking."""
    mlflow.set_tracking_uri('databricks')
    self.client = MlflowClient()
    
    # Set default experiment context from config
    try:
      from server.utils.config import get_config
      config = get_config()
      experiment_id = config.get('experiment_id')
      if experiment_id:
        mlflow.set_experiment(experiment_id=experiment_id)
    except Exception as e:
      # Don't fail initialization if config is unavailable
      pass

  def _safe_dict_conversion(self, obj):
    """Safely convert object to dict, handling various MLflow object types."""
    if obj is None:
      return None
    
    # If it's already a dict, return it
    if isinstance(obj, dict):
      return obj
    
    # Handle list inputs/outputs - wrap in a dict
    if isinstance(obj, list):
      return {"data": obj}
    
    # Handle string inputs/outputs - wrap in a dict  
    if isinstance(obj, str):
      return {"text": obj}
    
    # Handle numeric inputs/outputs - wrap in a dict
    if isinstance(obj, (int, float, bool)):
      return {"value": obj}
    
    # Try to convert to dict if it has items() method (like MLflow objects)
    if hasattr(obj, 'items'):
      try:
        return dict(obj.items())
      except Exception:
        pass
    
    # Try direct dict conversion
    try:
      return dict(obj)
    except Exception:
      pass
    
    # If all else fails, wrap the object in a dict
    return {"raw": str(obj)}

  def _extract_request_response_preview(self, trace) -> tuple[Optional[str], Optional[str]]:
    """Extract request and response previews from trace data.
    
    Returns:
        Tuple of (request_preview, response_preview)
    """
    request_preview = None
    response_preview = None
    
    try:
      # First try to get preview from trace metadata (most reliable)
      if hasattr(trace.info, 'request_metadata') and trace.info.request_metadata:
        import json
        
        # Try to get from mlflow.traceInputs
        trace_inputs = trace.info.request_metadata.get('mlflow.traceInputs', '')
        if trace_inputs:
          try:
            inputs = json.loads(trace_inputs) if isinstance(trace_inputs, str) else trace_inputs
            # Extract from messages array
            if isinstance(inputs, dict) and 'messages' in inputs:
              messages = inputs['messages']
              # Find the last user message
              for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get('role') == 'user':
                  content = msg.get('content', '')
                  request_preview = content[:200] + '...' if len(content) > 200 else content
                  break
          except (json.JSONDecodeError, Exception):
            pass
            
        # Try to get from mlflow.traceOutputs
        trace_outputs = trace.info.request_metadata.get('mlflow.traceOutputs', '')
        if trace_outputs:
          try:
            # Handle truncated JSON - if it ends with "..." it's likely truncated
            if isinstance(trace_outputs, str) and trace_outputs.endswith('...'):
              # Skip truncated data and fall through to span extraction
              pass
            else:
              outputs = json.loads(trace_outputs) if isinstance(trace_outputs, str) else trace_outputs
              # Extract from choices array
              if isinstance(outputs, dict) and 'choices' in outputs:
                choices = outputs['choices']
                if choices and isinstance(choices, list) and len(choices) > 0:
                  choice = choices[0]
                  if isinstance(choice, dict) and 'message' in choice:
                    content = choice['message'].get('content', '')
                    response_preview = content[:200] + '...' if len(content) > 200 else content
              # Also handle direct text output
              elif isinstance(outputs, dict) and 'text' in outputs:
                content = outputs['text']
                response_preview = content[:200] + '...' if len(content) > 200 else content
          except (json.JSONDecodeError, Exception):
            pass
      
      # Only return early if we got BOTH previews from metadata
      if request_preview and response_preview:
        return request_preview, response_preview
      # Always access spans to get previews
      if trace.data and trace.data.spans:
        # Find the first CHAT_MODEL span which typically contains the conversation
        for span in trace.data.spans:
          # Check for CHAT_MODEL spans using attributes since span_type might not be directly available
          attributes = getattr(span, 'attributes', {})
          mlflow_span_type = attributes.get('mlflow.spanType', '')
          
          if mlflow_span_type in ['CHAT_MODEL', 'AGENT']:
            # Extract request from attributes
            import json
            mlflow_inputs = attributes.get('mlflow.spanInputs', '')
            if mlflow_inputs:
              try:
                inputs = json.loads(mlflow_inputs) if isinstance(mlflow_inputs, str) else mlflow_inputs
                
                # Handle different input formats
                if isinstance(inputs, list) and len(inputs) > 0:
                  # First element might be messages array
                  messages = inputs[0] if isinstance(inputs[0], list) else inputs
                  # Find the last user message
                  for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get('type') == 'human':
                      content = msg.get('content', '')
                      request_preview = content[:200] + '...' if len(content) > 200 else content
                      break
                elif isinstance(inputs, dict):
                  # Check for messages in dict format
                  messages = inputs.get('messages', [])
                  if messages and isinstance(messages, list):
                    for msg in reversed(messages):
                      if isinstance(msg, dict) and msg.get('role') == 'user':
                        content = msg.get('content', '')
                        request_preview = content[:200] + '...' if len(content) > 200 else content
                        break
              except (json.JSONDecodeError, Exception) as e:
                pass
              
            # Extract response from attributes  
            mlflow_outputs = attributes.get('mlflow.spanOutputs', '')
            if mlflow_outputs:
              try:
                outputs = json.loads(mlflow_outputs) if isinstance(mlflow_outputs, str) else mlflow_outputs
                
                if isinstance(outputs, dict):
                  # Check for choices format (OpenAI/Agent format)
                  choices = outputs.get('choices', [])
                  if choices and isinstance(choices, list) and len(choices) > 0:
                    choice = choices[0]
                    if isinstance(choice, dict) and 'message' in choice:
                      message = choice['message']
                      if isinstance(message, dict):
                        content = message.get('content', '')
                        response_preview = content[:200] + '...' if len(content) > 200 else content
                  
                  # Check for generations format (Langchain)
                  if not response_preview:
                    generations = outputs.get('generations', [])
                    if generations and isinstance(generations, list) and len(generations) > 0:
                      gen_list = generations[0]
                      if isinstance(gen_list, list) and len(gen_list) > 0:
                        generation = gen_list[0]
                        if isinstance(generation, dict):
                          text = generation.get('text', '')
                          if text:
                            response_preview = text[:200] + '...' if len(text) > 200 else text
                          else:
                            # Try message format
                            message = generation.get('message', {})
                            if isinstance(message, dict):
                              content = message.get('content', '')
                              response_preview = content[:200] + '...' if len(content) > 200 else content
                  
                  # If no generations, try direct text field
                  if not response_preview and 'text' in outputs:
                    text = str(outputs['text'])
                    response_preview = text[:200] + '...' if len(text) > 200 else text
              except (json.JSONDecodeError, Exception) as e:
                pass
            
            # If we found previews, we're done
            if request_preview or response_preview:
              break
              
    except Exception as e:
      # Log but don't fail - previews are optional
      import logging
      logger = logging.getLogger(__name__)
      logger.debug(f"Failed to extract previews for trace {trace.info.trace_id}: {str(e)}")
    
    return request_preview, response_preview

  def search_traces(
    self,
    experiment_ids: List[str],
    filter_string: Optional[str] = None,
    run_id: Optional[str] = None,
    max_results: Optional[int] = 1000,
    order_by: Optional[List[str]] = None,
    page_token: Optional[str] = None,
    include_spans: Optional[bool] = False,
  ) -> Dict[str, Any]:
    """Search for traces in MLflow experiments.

    Args:
        experiment_ids: List of experiment IDs to search in
        filter_string: Optional filter string for traces
        run_id: Optional run ID to filter by
        max_results: Maximum number of results to return
        order_by: Optional list of fields to order by
        page_token: Optional pagination token

    Returns:
        Dictionary containing traces and pagination info
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    start_time = time.time()
    logger.info(f"🔍 [MLFLOW UTILS] Starting search_traces - experiments: {experiment_ids}, max_results: {max_results}, include_spans: {include_spans}, filter: {filter_string}")
    
    try:
      # Search for traces using the SDK
      sdk_start = time.time()
      
      # If searching by run_id without experiment_ids, we need to get the experiment from the run
      if run_id and not experiment_ids:
        try:
          run = mlflow.get_run(run_id)
          experiment_ids = [run.info.experiment_id]
          logger.info(f"🔍 [MLFLOW UTILS] Got experiment_id {experiment_ids[0]} from run {run_id}")
        except Exception as e:
          logger.warning(f"⚠️ [MLFLOW UTILS] Could not get experiment from run {run_id}: {str(e)}")
          # Fall back to using no experiment_ids
          experiment_ids = None
      
      traces = self.client.search_traces(
        experiment_ids=experiment_ids,
        filter_string=filter_string,
        run_id=run_id,
        max_results=max_results or 1000,
        order_by=order_by,
        page_token=page_token,
      )
      sdk_time = time.time() - sdk_start
      logger.info(f"📚 [MLFLOW UTILS] MLflow SDK search_traces took {sdk_time*1000:.1f}ms, returned {len(traces)} traces")

      # Convert SDK response to API format
      conversion_start = time.time()
      trace_list = []
      spans_processed = 0
      
      for trace in traces:
        # Extract request/response previews (always done regardless of include_spans)
        request_preview, response_preview = self._extract_request_response_preview(trace)
        
        # Convert trace info to match our Pydantic models
        trace_info = {
          'trace_id': trace.info.trace_id,
          'trace_location': {
            'experiment_id': trace.info.experiment_id,
            'run_id': trace.info.run_id if hasattr(trace.info, 'run_id') and trace.info.run_id else '',
          },
          'request_time': str(trace.info.timestamp_ms),
          'execution_duration': f'{trace.info.execution_time_ms}ms'
          if trace.info.execution_time_ms
          else '0ms',
          'state': trace.info.status or 'OK',
          'trace_metadata': dict(trace.info.request_metadata)
          if trace.info.request_metadata
          else {},
          'tags': dict(trace.info.tags) if trace.info.tags else {},
          'assessments': [],
          'request_preview': request_preview,
          'response_preview': response_preview,
        }

        # Convert trace data with proper span transformation (only if requested)
        trace_data = {'spans': []}
        if include_spans and trace.data and trace.data.spans:
          for span in trace.data.spans:
            # Transform MLflow span to match our Pydantic model
            span_dict = {
              'name': span.name,
              'span_id': span.span_id,
              'parent_id': span.parent_id,
              'start_time_ms': int(span.start_time_ns // 1_000_000) if span.start_time_ns else 0,
              'end_time_ms': int(span.end_time_ns // 1_000_000) if span.end_time_ns else 0,
              'status': {
                'status_code': 'OK' if span.status == 'OK' or not span.status else 'ERROR',
                'description': span.status_message if hasattr(span, 'status_message') and span.status_message else '',
              },
              'span_type': getattr(span, 'span_type', 'UNKNOWN'),
              'inputs': self._safe_dict_conversion(getattr(span, 'inputs', None)),
              'outputs': self._safe_dict_conversion(getattr(span, 'outputs', None)),
              'attributes': self._safe_dict_conversion(getattr(span, 'attributes', None)),
            }
            trace_data['spans'].append(span_dict)
            spans_processed += 1

        trace_list.append({'info': trace_info, 'data': trace_data})

      conversion_time = time.time() - conversion_start
      total_time = time.time() - start_time
      
      logger.info(f"🔄 [MLFLOW UTILS] Trace conversion took {conversion_time*1000:.1f}ms, processed {spans_processed} spans")
      logger.info(f"✅ [MLFLOW UTILS] Total search_traces time {total_time*1000:.1f}ms for {len(trace_list)} traces")

      return {
        'traces': trace_list,
        'next_page_token': None,  # MLflow SDK doesn't provide proper pagination
      }

    except Exception as e:
      error_time = time.time() - start_time
      logger.error(f"❌ [MLFLOW UTILS] search_traces failed after {error_time*1000:.1f}ms: {str(e)}")
      raise Exception(f'Failed to search traces: {str(e)}')

  def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
    """Get experiment details by ID.

    Args:
        experiment_id: The experiment ID

    Returns:
        Dictionary containing experiment details
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    start_time = time.time()
    logger.info(f"🔍 [MLFLOW UTILS] Starting get_experiment for {experiment_id}")
    
    try:
      # Use MLflow SDK instead of REST API
      experiment = mlflow.get_experiment(experiment_id)
      
      total_time = time.time() - start_time
      logger.info(f"✅ [MLFLOW UTILS] get_experiment completed in {total_time*1000:.1f}ms for {experiment_id}")
      
      # Convert to dictionary format matching REST API response
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
      logger.error(f"❌ [MLFLOW UTILS] get_experiment failed after {error_time*1000:.1f}ms for {experiment_id}: {str(e)}")
      raise

  def get_run(self, run_id: str) -> Dict[str, Any]:
    """Get run details by ID.

    Args:
        run_id: The run ID

    Returns:
        Dictionary containing run details
    """
    # Use MLflow SDK instead of REST API
    run = mlflow.get_run(run_id)
    
    # Convert to dictionary format matching REST API response
    return {
      'run': {
        'info': {
          'run_id': run.info.run_id,
          'run_uuid': run.info.run_id,  # SDK uses run_id for both
          'experiment_id': run.info.experiment_id,
          'run_name': run.info.run_name if hasattr(run.info, 'run_name') and run.info.run_name else run.data.tags.get('mlflow.runName', ''),
          'status': run.info.status,
          'start_time': run.info.start_time,
          'end_time': run.info.end_time if hasattr(run.info, 'end_time') else None,
          'artifact_uri': run.info.artifact_uri,
          'lifecycle_stage': run.info.lifecycle_stage,
        },
        'data': {
          'metrics': [{'key': k, 'value': v.value, 'timestamp': v.timestamp, 'step': v.step} 
                      for k, v in run.data.metrics.items()],
          'params': [{'key': k, 'value': v} for k, v in run.data.params.items()],
          'tags': [{'key': k, 'value': v} for k, v in run.data.tags.items()],
        },
        'inputs': run.inputs.dataset_inputs if hasattr(run, 'inputs') and run.inputs and hasattr(run.inputs, 'dataset_inputs') else {},
        'outputs': run.outputs.__dict__ if hasattr(run, 'outputs') and run.outputs else {},
      }
    }

  def create_run(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new MLflow run.

    Args:
        data: Run creation data

    Returns:
        Dictionary containing created run details
    """
    # Use MLflow SDK instead of REST API
    experiment_id = data.get('experiment_id')
    run_name = data.get('run_name')
    tags = data.get('tags', {})
    
    # Add run_name to tags if provided
    if run_name:
      tags['mlflow.runName'] = run_name
    
    # Create run using SDK
    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name, tags=tags) as run:
      run_id = run.info.run_id
    
    # Return the created run details
    return self.get_run(run_id)

  def update_run(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an MLflow run.

    Args:
        data: Run update data

    Returns:
        Dictionary containing updated run details
    """
    # Use MLflow SDK instead of REST API
    run_id = data.get('run_id')
    status = data.get('status')
    end_time = data.get('end_time')
    
    # Update run using MlflowClient
    if status:
      self.client.set_terminated(run_id, status, end_time)
    
    # Update tags if provided
    if 'tags' in data:
      for tag in data['tags']:
        self.client.set_tag(run_id, tag['key'], tag['value'])
    
    return {'message': 'Run updated successfully'}

  def search_runs(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Search for runs in experiments.

    Args:
        data: Search parameters

    Returns:
        Dictionary containing search results
    """
    # Use MLflow SDK instead of REST API
    experiment_ids = data.get('experiment_ids', [])
    filter_string = data.get('filter', '')
    max_results = data.get('max_results', 1000)
    order_by = data.get('order_by', [])
    page_token = data.get('page_token')
    
    # Search runs using SDK
    runs_df = mlflow.search_runs(
      experiment_ids=experiment_ids,
      filter_string=filter_string,
      max_results=max_results,
      order_by=order_by,
      page_token=page_token
    )
    
    # Convert DataFrame to dictionary format matching REST API response
    runs = []
    for _, row in runs_df.iterrows():
      run_data = row.to_dict()
      runs.append({
        'info': {
          'run_id': run_data.get('run_id'),
          'experiment_id': run_data.get('experiment_id'),
          'status': run_data.get('status'),
          'start_time': run_data.get('start_time'),
          'end_time': run_data.get('end_time'),
          'artifact_uri': run_data.get('artifact_uri'),
          'lifecycle_stage': run_data.get('lifecycle_stage'),
        },
        'data': {
          'metrics': [],  # Not included in search results
          'params': [],   # Not included in search results
          'tags': [{'key': k.replace('tags.', ''), 'value': v} 
                   for k, v in run_data.items() if k.startswith('tags.')],
        }
      })
    
    return {
      'runs': runs,
      'next_page_token': None  # SDK doesn't return page tokens in the same way
    }

  def link_traces_to_run(self, run_id: str, trace_ids: List[str]) -> Dict[str, Any]:
    """Link traces to an MLflow run.

    Args:
        run_id: The MLflow run ID to link traces to
        trace_ids: List of trace IDs to link

    Returns:
        Dictionary containing link operation result
    """
    url = get_mlflow_api_url('/traces/link-to-run')
    data = {'run_id': run_id, 'trace_ids': trace_ids}
    return fetch_databricks_sync(method='POST', url=url, data=data)

  def get_trace(self, trace_id: str) -> Dict[str, Any]:
    """Get trace information by ID.

    Args:
        trace_id: The trace ID

    Returns:
        Dictionary containing trace details
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    start_time = time.time()
    logger.info(f"🔍 [MLFLOW UTILS] Starting MLflow SDK get_trace for {trace_id}")
    
    try:
      # Use MLflow SDK to get the trace
      sdk_start = time.time()
      trace = self.client.get_trace(trace_id)
      sdk_time = time.time() - sdk_start
      logger.info(f"📚 [MLFLOW UTILS] MLflow SDK client.get_trace took {sdk_time*1000:.1f}ms for {trace_id}")

      # Convert the trace object to a dictionary format similar to the API response
      convert_start = time.time()
      trace_dict = {
        'info': {
          'trace_id': trace.info.trace_id,
          'experiment_id': trace.info.experiment_id,
          'request_time': str(int(trace.info.timestamp_ms)),
          'execution_duration': f'{trace.info.execution_time_ms}ms'
          if trace.info.execution_time_ms
          else None,
          'state': trace.info.status.value if trace.info.status else 'UNKNOWN',
          'request_id': trace.info.request_id if hasattr(trace.info, 'request_id') else None,
        },
        'data': {'spans': []},
      }

      # Add spans data if available
      spans_processed = 0
      if hasattr(trace, 'data') and trace.data and hasattr(trace.data, 'spans'):
        for span in trace.data.spans:
          # Convert nanoseconds to milliseconds safely
          start_time_ms = int(span.start_time_ns // 1_000_000) if span.start_time_ns else 0
          end_time_ms = int(span.end_time_ns // 1_000_000) if span.end_time_ns else start_time_ms
          
          span_dict = {
            'span_id': span.span_id,
            'name': span.name,
            'start_time_ms': start_time_ms,
            'end_time_ms': end_time_ms,
            'parent_id': span.parent_id,
            'attributes': dict(span.attributes) if span.attributes else {},
            'inputs': self._safe_dict_conversion(span.inputs if hasattr(span, 'inputs') else None),
            'outputs': self._safe_dict_conversion(span.outputs if hasattr(span, 'outputs') else None),
            'span_type': span.span_type if hasattr(span, 'span_type') else span.attributes.get('mlflow.spanType', 'UNKNOWN') if span.attributes else 'UNKNOWN',
            'status': {
              'status_code': 'OK' if not hasattr(span, 'status') or span.status == 'OK' or not span.status else 'ERROR',
              'description': span.status_message if hasattr(span, 'status_message') and span.status_message else '',
            }
          }
          trace_dict['data']['spans'].append(span_dict)
          spans_processed += 1

      convert_time = time.time() - convert_start
      total_time = time.time() - start_time
      
      logger.info(f"🔄 [MLFLOW UTILS] Data conversion took {convert_time*1000:.1f}ms, processed {spans_processed} spans")
      logger.info(f"✅ [MLFLOW UTILS] Total get_trace time {total_time*1000:.1f}ms for {trace_id}")

      return trace_dict

    except Exception as e:
      error_time = time.time() - start_time
      logger.error(f"❌ [MLFLOW UTILS] get_trace failed after {error_time*1000:.1f}ms for {trace_id}: {str(e)}")
      raise Exception(f'Trace not found: {str(e)}')

  def get_trace_data(self, trace_id: str) -> Dict[str, Any]:
    """Get trace data (spans) by trace ID.

    Args:
        trace_id: The trace ID

    Returns:
        Dictionary containing trace data
    """
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

  def log_feedback(self, trace_id: str, key: str, value: Any, username: str, comment: Optional[str] = None) -> Dict[str, Any]:
    """Log feedback on a trace.

    Args:
        trace_id: The trace ID
        key: The feedback key
        value: The feedback value (can be str, int, float, bool, or dict)
        username: The username of the person providing feedback
        comment: Optional comment about the feedback

    Returns:
        Dictionary containing operation result
    """
    try:
      from mlflow.entities import AssessmentSource
      
      # Log feedback using MLflow with user identity
      assessment = mlflow.log_feedback(
        trace_id=trace_id,
        name=key,
        value=value,
        source=AssessmentSource(source_type="human", source_id=username),
        rationale=comment
      )
      
      return {
        'success': True,
        'message': f'Feedback logged successfully for trace {trace_id} by user {username}'
      }
    except Exception as e:
      raise Exception(f'Failed to log feedback: {str(e)}')

  def log_expectation(self, trace_id: str, key: str, value: Any, username: str, comment: Optional[str] = None) -> Dict[str, Any]:
    """Log expectation on a trace.

    Args:
        trace_id: The trace ID
        key: The expectation key
        value: The expectation value (can be str, int, float, bool, or dict)
        username: The username of the person providing expectation
        comment: Optional comment about the expectation

    Returns:
        Dictionary containing operation result
    """
    try:
      from mlflow.entities import AssessmentSource
      
      # Prepare metadata if comment is provided
      metadata = {'comment': comment} if comment else None
      
      # Log expectation using MLflow with user identity
      assessment = mlflow.log_expectation(
        trace_id=trace_id,
        name=key,
        value=value,
        source=AssessmentSource(source_type="human", source_id=username),
        metadata=metadata
      )
      
      return {
        'success': True,
        'message': f'Expectation logged successfully for trace {trace_id} by user {username}'
      }
    except Exception as e:
      raise Exception(f'Failed to log expectation: {str(e)}')


# Create a global instance for easy access
mlflow_utils = MLflowUtils()
