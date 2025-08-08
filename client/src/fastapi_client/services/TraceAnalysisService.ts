/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TraceAnalysisResponse } from "../models/TraceAnalysisResponse";
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
export class TraceAnalysisService {
  /**
   * Analyze Trace Patterns Endpoint
   * Analyze patterns in recent traces to understand agent architecture and workflows.
   *
   * This endpoint examines the structure of traces to identify:
   * - Span types and hierarchy patterns
   * - Tool usage and calling patterns
   * - Conversation flow and message formats
   * - Input/output data structures
   * - Agent workflow patterns (RAG, function calling, etc.)
   * @param limit Number of recent traces to analyze
   * @param experimentId Experiment ID to analyze (defaults to config experiment_id)
   * @returns TraceAnalysisResponse Successful Response
   * @throws ApiError
   */
  public static analyzeTracePatternsEndpointApiTracesAnalyzePatternsGet(
    limit: number = 10,
    experimentId?: string | null
  ): CancelablePromise<TraceAnalysisResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/traces/analyze-patterns",
      query: {
        limit: limit,
        experiment_id: experimentId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
