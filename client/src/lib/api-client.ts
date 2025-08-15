/**
 * Enhanced API client with error handling and toast notifications.
 *
 * This module wraps the auto-generated FastAPI client to provide:
 * - Automatic error handling with toast notifications
 * - Request/response interceptors
 * - Type-safe API calls
 * - Consistent error formatting
 */

import { toast } from "sonner";
import { ReviewApp, LabelingSession, LabelingItem, JsonValue } from "@/types/renderers";
import {
  CoreService,
  ReviewAppsService,
  LabelingSessionsService,
  LabelingItemsService,
  MLflowService,
  OpenAPI,
  ApiService,
} from "@/fastapi_client";

// Configure the OpenAPI client - use relative URLs (Vite proxies /api to localhost:8000 in dev)
OpenAPI.BASE = "";

interface ApiError {
  error: {
    message: string;
    code: string;
    details: Record<string, unknown>;
  };
  request_id: string;
  status_code: number;
}

class ApiClientWrapper {
  constructor() {
    // Disable interceptors temporarily to isolate the issue
    // this.setupInterceptors();
  }

  private setupInterceptors() {
    // Add response interceptor to handle errors
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);

        // Check if this is an API call
        const url = args[0] as string;
        if (url.includes("/api/")) {
          // Handle error responses
          if (!response.ok) {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
              try {
                // Clone the response to avoid consuming the stream
                const responseClone = response.clone();
                const errorData: ApiError = await responseClone.json();
                this.handleApiError(errorData);
                // Return the original response so it can still be consumed
                return response;
              } catch {
                // If we can't parse the error, show a generic message
                toast.error(`Request failed: ${response.statusText}`);
              }
            }
          }
        }

        return response;
      } catch (error) {
        // Handle network errors, CORS issues, etc.
        const url = args[0] as string;
        if (url.includes("/api/")) {
          console.error("Network error for API call:", error);
          toast.error("Network error. Please check your connection.");
        }
        throw error; // Re-throw the error so the original caller can handle it
      }
    };
  }

  private handleApiError(error: ApiError) {
    // Show user-friendly error message
    const message = error.error.message || "An unexpected error occurred";

    // Log detailed error for debugging
    console.error("API Error:", {
      message: error.error.message,
      code: error.error.code,
      details: error.error.details,
      request_id: error.request_id,
      status_code: error.status_code,
    });

    // Show toast based on error type
    switch (error.status_code) {
      case 400:
        toast.error(`Validation Error: ${message}`);
        break;
      case 401:
        toast.error("Authentication required");
        break;
      case 403:
        toast.error("You do not have permission to perform this action");
        break;
      case 404:
        toast.error(`Not found: ${message}`);
        break;
      case 502:
        toast.error("Databricks API error. Please try again later.");
        break;
      default:
        toast.error(message);
    }
  }

  // Provide access to individual services
  get api() {
    return {
      // Manifest endpoint (unified config, user, and workspace info)
      getManifest: () => CoreService.getAppManifestApiManifestGet(),

      // Review Apps endpoints
      listReviewApps: (params?: { filter?: string; pageSize?: number }) =>
        ReviewAppsService.listReviewAppsApiReviewAppsGet(params?.filter, params?.pageSize),
      getReviewApp: (params: { reviewAppId: string }) =>
        ReviewAppsService.getReviewAppApiReviewAppsReviewAppIdGet(params.reviewAppId),
      createReviewApp: (params: { reviewApp: Partial<ReviewApp> }) =>
        ReviewAppsService.createReviewAppApiReviewAppsPost(params.reviewApp),
      updateReviewApp: (params: {
        reviewAppId: string;
        reviewApp: Partial<ReviewApp>;
        updateMask: string;
      }) =>
        ReviewAppsService.updateReviewAppApiReviewAppsReviewAppIdPatch(
          params.reviewAppId,
          params.reviewApp,
          params.updateMask
        ),

      // Labeling Sessions endpoints
      listLabelingSessions: (params: { reviewAppId: string }) =>
        LabelingSessionsService.listLabelingSessionsApiReviewAppsReviewAppIdLabelingSessionsGet(
          params.reviewAppId
        ),
      getLabelingSession: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingSessionsService.getLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdGet(
          params.reviewAppId,
          params.sessionId
        ),
      createLabelingSession: (params: { reviewAppId: string; session: Partial<LabelingSession> }) =>
        LabelingSessionsService.createLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsPost(
          params.reviewAppId,
          params.session
        ),
      updateLabelingSession: (params: {
        reviewAppId: string;
        sessionId: string;
        session: Partial<LabelingSession>;
        updateMask: string;
      }) =>
        LabelingSessionsService.updateLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdPatch(
          params.reviewAppId,
          params.sessionId,
          params.session,
          params.updateMask
        ),
      deleteLabelingSession: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingSessionsService.deleteLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdDelete(
          params.reviewAppId,
          params.sessionId
        ),

      // Labeling Items endpoints (no longer need reviewAppId - uses cached app)
      listLabelingItems: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingItemsService.listItemsApiLabelingSessionsLabelingSessionIdItemsGet(
          params.sessionId
        ),
      updateLabelingItem: (params: {
        reviewAppId: string;
        sessionId: string;
        itemId: string;
        item: Partial<LabelingItem>;
        updateMask: string;
      }) =>
        LabelingItemsService.updateItemApiLabelingSessionsLabelingSessionIdItemsItemIdPatch(
          params.sessionId,
          params.itemId,
          params.updateMask,
          params.item
        ),
      deleteLabelingItem: (params: { reviewAppId: string; sessionId: string; itemId: string }) =>
        LabelingItemsService.deleteItemApiLabelingSessionsLabelingSessionIdItemsItemIdDelete(
          params.sessionId,
          params.itemId
        ),

      // MLflow endpoints
      searchTraces: (params: Record<string, unknown>) =>
        MLflowService.searchTracesApiMlflowSearchTracesPost(params),
      getTrace: (params: { traceId: string }) =>
        MLflowService.getTraceApiMlflowTracesTraceIdGet(params.traceId),
      linkTracesToRun: (params: { runId: string; traceIds: string[] }) =>
        MLflowService.linkTracesToRunApiMlflowTracesLinkToRunPost(params),
      linkTracesToSession: (params: {
        reviewAppId: string;
        sessionId: string;
        mlflow_run_id: string;
        trace_ids: string[];
      }) =>
        LabelingSessionsService.linkTracesToSessionApiLabelingSessionsLabelingSessionIdLinkTracesPost(
          params.sessionId,
          { mlflow_run_id: params.mlflow_run_id, trace_ids: params.trace_ids }
        ),
      getRun: (params: { runId: string }) =>
        MLflowService.getRunApiMlflowRunsRunIdGet(params.runId),
      createRun: (params: Record<string, unknown>) =>
        MLflowService.createRunApiMlflowRunsPost(params),
      updateRun: (params: Record<string, unknown>) =>
        MLflowService.updateRunApiMlflowRunsUpdatePost(params),

      // MLflow Feedback and Expectation endpoints
      logTraceFeedback: (params: {
        traceId: string;
        name: string;
        value: JsonValue;
        rationale?: string;
      }) =>
        MLflowService.logTraceFeedbackApiMlflowTracesTraceIdFeedbackPost(params.traceId, {
          assessment: {
            name: params.name,
            value: params.value,
            rationale: params.rationale,
          },
        }),
      updateTraceFeedback: (params: {
        traceId: string;
        assessment_id: string;
        value: JsonValue;
        rationale?: string;
      }) =>
        MLflowService.updateTraceFeedbackApiMlflowTracesTraceIdFeedbackPatch(params.traceId, {
          assessment_id: params.assessment_id,
          assessment: {
            name: '', // Name not needed for updates as it's tied to assessment_id
            value: params.value,
            rationale: params.rationale,
          },
        }),
      logTraceExpectation: (params: {
        traceId: string;
        name: string;
        value: JsonValue;
        rationale?: string;
      }) =>
        MLflowService.logTraceExpectationApiMlflowTracesTraceIdExpectationPost(params.traceId, {
          assessment: {
            name: params.name,
            value: params.value,
            rationale: params.rationale,
          },
        }),
      updateTraceExpectation: (params: {
        traceId: string;
        assessment_id: string;
        value: JsonValue;
        rationale?: string;
      }) =>
        MLflowService.updateTraceExpectationApiMlflowTracesTraceIdExpectationPatch(params.traceId, {
          assessment_id: params.assessment_id,
          assessment: {
            name: '', // Name not needed for updates as it's tied to assessment_id
            value: params.value,
            rationale: params.rationale,
          },
        }),

      // Analysis endpoints
      getSessionAnalysis: (params: { reviewAppId: string; sessionId: string }) =>
        ApiService.getSessionAnalysisApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisGet(
          params.reviewAppId,
          params.sessionId
        ),
      getAnalysisStatus: (params: { reviewAppId: string; sessionId: string }) =>
        ApiService.getAnalysisStatusApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisStatusGet(
          params.reviewAppId,
          params.sessionId
        ),
      triggerSessionAnalysis: (params: {
        reviewAppId: string;
        sessionId: string;
        include_ai_insights?: boolean;
        model_endpoint?: string;
      }) =>
        ApiService.triggerSessionAnalysisApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisTriggerPost(
          params.reviewAppId,
          params.sessionId,
          {
            include_ai_insights: params.include_ai_insights ?? true,
            model_endpoint: params.model_endpoint ?? "databricks-claude-sonnet-4",
          }
        ),

      // Experiment Analysis endpoints
      getExperimentSummary: (experimentId: string) =>
        ApiService.getExperimentSummaryApiExperimentSummaryExperimentIdGet(experimentId),
      triggerAnalysisApiExperimentSummaryTriggerAnalysisPost: (params: {
        experiment_id: string;
        focus?: string;
        trace_sample_size?: number;
        model_endpoint?: string;
      }) =>
        ApiService.triggerAnalysisApiExperimentSummaryTriggerAnalysisPost(params),
      getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet: (experimentId: string) =>
        ApiService.getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet(experimentId),
    };
  }
}

// Export a singleton instance
export const apiClient = new ApiClientWrapper();
