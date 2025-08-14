/**
 * MLflow native types - matches the exact structure returned by MLflow's to_dict()
 */

// ============ Trace Location Types ============
export interface MLflowExperiment {
  experiment_id: string;
}

export interface TraceLocation {
  type: 'MLFLOW_EXPERIMENT';
  mlflow_experiment: MLflowExperiment;
}

// ============ Span Types ============
export interface SpanStatus {
  message: string;
  code: 'STATUS_CODE_OK' | 'STATUS_CODE_ERROR' | string;
}

export interface SpanAttributes {
  'mlflow.traceRequestId'?: string;
  'mlflow.spanFunctionName'?: string;
  'mlflow.spanInputs'?: string;
  'mlflow.spanType'?: string;
  'mlflow.spanOutputs'?: string;
  [key: string]: string | undefined;
}

export interface MLflowSpan {
  trace_id: string;
  span_id: string;
  trace_state: string;
  parent_span_id: string;
  name: string;
  start_time_unix_nano: number;
  end_time_unix_nano: number;
  attributes: SpanAttributes;
  status: SpanStatus;
}

// ============ Trace Info Types ============
export interface TraceMetadata {
  'mlflow.databricks.workspaceID'?: string;
  'mlflow.databricks.workspaceURL'?: string;
  'mlflow.databricks.webappURL'?: string;
  'mlflow.databricks.notebook.commandID'?: string;
  'mlflow.databricks.notebookID'?: string;
  'mlflow.databricks.notebookPath'?: string;
  'mlflow.trace.sizeBytes'?: string;
  'mlflow.trace.user'?: string;
  'mlflow.trace.session'?: string;
  'mlflow.trace.sizeStats'?: string;
  'mlflow.trace_schema.version'?: string;
  'mlflow.traceInputs'?: string;
  'mlflow.traceOutputs'?: string;
  'mlflow.source.name'?: string;
  'mlflow.source.type'?: string;
  'mlflow.user'?: string;
  [key: string]: string | undefined;
}

export interface TraceTags {
  'mlflow.artifactLocation'?: string;
  'mlflow.traceName'?: string;
  'mlflow.user'?: string;
  [key: string]: string | undefined;
}

export interface MLflowTraceInfo {
  trace_id: string;
  client_request_id: string;
  trace_location: TraceLocation;
  request_time: string;
  state: 'OK' | 'ERROR' | string;
  trace_metadata: TraceMetadata;
  tags: TraceTags;
  request_preview?: string;
  response_preview?: string;
  execution_duration_ms?: number;
}

// ============ Trace Data Types ============
export interface MLflowTraceData {
  spans: MLflowSpan[];
}

// ============ Full Trace Type ============
export interface MLflowTrace {
  info: MLflowTraceInfo;
  data: MLflowTraceData;
}

// ============ API Response Types ============
export interface SearchTracesResponse {
  traces: MLflowTrace[];
  next_page_token: string | null;
}

// ============ Request Types ============
export interface SearchTracesRequest {
  experiment_ids?: string[];
  filter?: string;
  run_id?: string;
  max_results?: number;
  page_token?: string;
  order_by?: string[];
  include_spans?: boolean;
}