/**
 * Transform utilities for MLflow data
 * Converts MLflow's native format to frontend-compatible format
 */

import type { MLflowTrace, MLflowSpan } from "@/types/mlflow";

/**
 * Transforms an MLflow span from nanosecond timestamps to millisecond timestamps
 * and adds computed fields expected by the frontend
 */
function transformSpan(span: MLflowSpan): any {
  const attributes = span.attributes || {};

  return {
    ...span,
    // Convert nanosecond timestamps to milliseconds
    start_time_ms: Math.floor(span.start_time_unix_nano / 1_000_000),
    end_time_ms: Math.floor(span.end_time_unix_nano / 1_000_000),
    // Map span type from attributes if not directly present
    span_type: attributes["mlflow.spanType"] || "UNKNOWN",
    // Parse inputs/outputs from attributes if present
    inputs: (() => {
      try {
        return attributes["mlflow.spanInputs"]
          ? JSON.parse(attributes["mlflow.spanInputs"] as string)
          : undefined;
      } catch {
        return attributes["mlflow.spanInputs"];
      }
    })(),
    outputs: (() => {
      try {
        return attributes["mlflow.spanOutputs"]
          ? JSON.parse(attributes["mlflow.spanOutputs"] as string)
          : undefined;
      } catch {
        return attributes["mlflow.spanOutputs"];
      }
    })(),
    // Keep original fields for compatibility
    attributes,
    status: {
      status_code: span.status?.code || "STATUS_CODE_OK",
      description: span.status?.message || "",
    },
  };
}

/**
 * Transforms an MLflow trace from native format to frontend-compatible format
 */
export function transformTrace(trace: MLflowTrace | any): any {
  if (!trace) return trace;

  // If trace already has the correct structure (from search-traces), just transform spans
  if (trace.info && trace.data) {
    return {
      info: {
        ...trace.info,
        // Keep execution_duration_ms as is (MLflow already provides it)
        execution_duration: trace.info.execution_duration_ms
          ? `${trace.info.execution_duration_ms}ms`
          : undefined,
      },
      data: {
        spans: trace.data?.spans?.map(transformSpan) || [],
      },
    };
  }

  // Otherwise assume it's a raw MLflow trace object
  return {
    info: {
      ...trace.info,
      // Keep execution_duration_ms as is (MLflow already provides it)
      execution_duration: trace.info?.execution_duration_ms
        ? `${trace.info.execution_duration_ms}ms`
        : undefined,
    },
    data: {
      spans: trace.data?.spans?.map(transformSpan) || [],
    },
  };
}

/**
 * Transforms search traces response
 * The traces already come with info and data at the top level
 */
export function transformSearchTracesResponse(response: any): any {
  if (!response?.traces) return response;

  // Traces from search-traces already have the correct structure
  // We just need to transform the spans inside
  return {
    ...response,
    traces: response.traces.map((trace: any) => ({
      info: trace.info,
      data: {
        spans: trace.data?.spans?.map(transformSpan) || [],
      },
    })),
  };
}
