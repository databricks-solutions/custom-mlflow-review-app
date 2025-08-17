/**
 * MLflow Trace types - matches the exact structure from MLflow's to_dict()
 * Based on MLflow source: mlflow/entities/trace.py
 */

// ============ Trace State Enum ============
export enum TraceState {
  STATE_UNSPECIFIED = "STATE_UNSPECIFIED",
  OK = "OK",
  ERROR = "ERROR",
  IN_PROGRESS = "IN_PROGRESS"
}

// ============ Trace Location Types ============
export enum TraceLocationType {
  TRACE_LOCATION_TYPE_UNSPECIFIED = "TRACE_LOCATION_TYPE_UNSPECIFIED",
  MLFLOW_EXPERIMENT = "MLFLOW_EXPERIMENT",
  INFERENCE_TABLE = "INFERENCE_TABLE"
}

export interface MlflowExperimentLocation {
  experiment_id: string;
}

export interface InferenceTableLocation {
  table_name?: string;
}

export interface TraceLocation {
  type: TraceLocationType;
  mlflow_experiment?: MlflowExperimentLocation | null;
  inference_table?: InferenceTableLocation | null;
}

// ============ Span Types ============
export enum SpanType {
  LLM = "LLM",
  CHAIN = "CHAIN",
  AGENT = "AGENT",
  TOOL = "TOOL",
  CHAT_MODEL = "CHAT_MODEL",
  RETRIEVER = "RETRIEVER",
  PARSER = "PARSER",
  EMBEDDING = "EMBEDDING",
  RERANKER = "RERANKER",
  MEMORY = "MEMORY",
  UNKNOWN = "UNKNOWN"
}

export enum SpanStatusCode {
  UNSET = "UNSET",
  OK = "OK",
  ERROR = "ERROR"
}

export interface SpanStatus {
  status_code: SpanStatusCode;
  description: string;
}

export interface SpanEvent {
  name: string;
  timestamp: number;
  attributes?: Record<string, any>;
}

export interface Span {
  // Required fields
  trace_id: string;
  span_id: string;
  name: string;
  start_time_ns: number; // Nanoseconds
  end_time_ns: number; // Nanoseconds
  span_type: SpanType;
  
  // Optional fields
  parent_id?: string | null;
  status: SpanStatus;
  inputs?: any;
  outputs?: any;
  attributes?: Record<string, any>;
  events?: SpanEvent[];
}

// ============ Assessment Types ============
export enum AssessmentSourceType {
  SOURCE_TYPE_UNSPECIFIED = "SOURCE_TYPE_UNSPECIFIED",
  LLM_JUDGE = "LLM_JUDGE",
  HUMAN = "HUMAN",
  CODE = "CODE"
}

export interface AssessmentSource {
  source_type: AssessmentSourceType;
  source_id?: string | null;
}

export interface AssessmentError {
  error_code?: string;
  message?: string;
}

export interface ExpectationValue {
  value: any;
}

export interface FeedbackValue {
  value: any;
  error?: AssessmentError | null;
}

export interface Assessment {
  // Required fields
  name: string;
  source: AssessmentSource;
  
  // Optional associations
  trace_id?: string | null;
  run_id?: string | null;
  span_id?: string | null;
  
  // Assessment content
  rationale?: string | null;
  metadata?: Record<string, string> | null;
  expectation?: ExpectationValue | null;
  feedback?: FeedbackValue | null;
  
  // System fields
  create_time_ms?: number | null;
  last_update_time_ms?: number | null;
  assessment_id?: string | null;
  error?: AssessmentError | null;
  overrides?: string | null;
  valid?: boolean | null;
}

// ============ Trace Info Type ============
export interface TraceInfo {
  // Required fields
  trace_id: string;
  trace_location: TraceLocation;
  request_time: number; // Unix timestamp in milliseconds
  state: TraceState;
  
  // Optional fields
  request_preview?: string | null;
  response_preview?: string | null;
  client_request_id?: string | null;
  execution_duration?: number | null; // Duration in milliseconds
  trace_metadata: Record<string, string>; // Default: {}
  tags: Record<string, string>; // Default: {}
  assessments: Assessment[]; // Default: []
}

// ============ Trace Data Type ============
export interface TraceData {
  spans: Span[]; // Default: []
  
  // Computed properties for backward compatibility
  request?: any;
  response?: any;
  intermediate_outputs?: any;
}

// ============ Main Trace Type ============
export interface Trace {
  info: TraceInfo;
  data: TraceData;
}

// ============ API Response Types ============
export interface SearchTracesResponse {
  traces: Trace[];
  next_page_token: string | null;
}

// ============ API Request Types ============
export interface SearchTracesRequest {
  experiment_ids?: string[];
  filter?: string;
  run_id?: string;
  max_results?: number;
  page_token?: string;
  order_by?: string[];
  include_spans?: boolean;
}