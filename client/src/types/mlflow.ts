/**
 * MLflow types - Re-exports from mlflow-trace.ts for backward compatibility
 * New code should import directly from mlflow-trace.ts
 */

// Re-export everything from the new mlflow-trace module
export * from "./mlflow-trace";

// Legacy exports for backward compatibility
export type {
  Trace as MLflowTrace,
  TraceInfo as MLflowTraceInfo,
  TraceData as MLflowTraceData,
  Span as MLflowSpan,
  Assessment as MLflowAssessment,
} from "./mlflow-trace";

// Keep the old interfaces that might be used elsewhere
export interface TraceMetadata extends Record<string, string | undefined> {
  "mlflow.databricks.workspaceID"?: string;
  "mlflow.databricks.workspaceURL"?: string;
  "mlflow.databricks.webappURL"?: string;
  "mlflow.databricks.notebook.commandID"?: string;
  "mlflow.databricks.notebookID"?: string;
  "mlflow.databricks.notebookPath"?: string;
  "mlflow.trace.sizeBytes"?: string;
  "mlflow.trace.user"?: string;
  "mlflow.trace.session"?: string;
  "mlflow.trace.sizeStats"?: string;
  "mlflow.trace_schema.version"?: string;
  "mlflow.traceInputs"?: string;
  "mlflow.traceOutputs"?: string;
  "mlflow.source.name"?: string;
  "mlflow.source.type"?: string;
  "mlflow.user"?: string;
}

export interface TraceTags extends Record<string, string | undefined> {
  "mlflow.artifactLocation"?: string;
  "mlflow.traceName"?: string;
  "mlflow.user"?: string;
}