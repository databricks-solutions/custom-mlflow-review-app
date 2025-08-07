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
import {
  ConfigurationService,
  UserService,
  ReviewAppsService,
  LabelingSessionsService,
  LabelingItemsService,
  MLflowService,
  OpenAPI,
  ApiService
} from "@/fastapi_client";

// Configure the OpenAPI client - use relative URLs (Vite proxies /api to localhost:8000 in dev)
OpenAPI.BASE = '';

interface ApiError {
  error: {
    message: string;
    code: string;
    details: Record<string, any>;
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
      // Configuration endpoints
      getConfig: () => ConfigurationService.getConfigApiConfigGet(),
      getExperimentId: () => ConfigurationService.getExperimentIdApiConfigExperimentIdGet(),
      
      // User endpoints
      getCurrentUser: () => UserService.getCurrentUserApiUserMeGet(),
      getUserWorkspace: () => UserService.getUserWorkspaceInfoApiUserMeWorkspaceGet(),
      
      // Review Apps endpoints
      listReviewApps: (params?: { filter?: string; pageSize?: number }) => 
        ReviewAppsService.listReviewAppsApiReviewAppsGet(params?.filter, params?.pageSize),
      getCurrentReviewApp: () =>
        ReviewAppsService.getCurrentReviewAppApiReviewAppsCurrentGet(),
      getReviewApp: (params: { reviewAppId: string }) =>
        ReviewAppsService.getReviewAppApiReviewAppsReviewAppIdGet(params.reviewAppId),
      createReviewApp: (params: { reviewApp: any }) =>
        ReviewAppsService.createReviewAppApiReviewAppsPost(params.reviewApp),
      updateReviewApp: (params: { reviewAppId: string; reviewApp: any; updateMask: string }) =>
        ReviewAppsService.updateReviewAppApiReviewAppsReviewAppIdPatch(
          params.reviewAppId, params.reviewApp, params.updateMask
        ),
      
      // Labeling Sessions endpoints
      listLabelingSessions: (params: { reviewAppId: string }) =>
        LabelingSessionsService.listLabelingSessionsApiReviewAppsReviewAppIdLabelingSessionsGet(params.reviewAppId),
      getLabelingSession: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingSessionsService.getLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdGet(
          params.reviewAppId, params.sessionId
        ),
      createLabelingSession: (params: { reviewAppId: string; session: any }) =>
        LabelingSessionsService.createLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsPost(
          params.reviewAppId, params.session
        ),
      updateLabelingSession: (params: { reviewAppId: string; sessionId: string; session: any; updateMask: string }) =>
        LabelingSessionsService.updateLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdPatch(
          params.reviewAppId, params.sessionId, params.session, params.updateMask
        ),
      deleteLabelingSession: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingSessionsService.deleteLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdDelete(
          params.reviewAppId, params.sessionId
        ),
      
      // Labeling Items endpoints
      listLabelingItems: (params: { reviewAppId: string; sessionId: string }) =>
        LabelingItemsService.listItemsApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsGet(
          params.reviewAppId, params.sessionId
        ),
      updateLabelingItem: (params: { reviewAppId: string; sessionId: string; itemId: string; item: any; updateMask: string }) =>
        LabelingItemsService.updateItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdPatch(
          params.reviewAppId, params.sessionId, params.itemId, params.updateMask, params.item
        ),
      deleteLabelingItem: (params: { reviewAppId: string; sessionId: string; itemId: string }) =>
        ApiService.deleteItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdDelete(
          params.reviewAppId, params.sessionId, params.itemId
        ),
      
      // MLflow endpoints
      searchTraces: (params: any) =>
        MLflowService.searchTracesApiMlflowSearchTracesPost(params),
      getTrace: (params: { traceId: string; runId?: string }) =>
        MLflowService.getTraceApiMlflowTracesTraceIdGet(params.traceId, params.runId),
      getTraceMetadata: (params: { traceId: string }) =>
        MLflowService.getTraceMetadataApiMlflowTracesTraceIdMetadataGet(params.traceId),
      linkTracesToRun: (params: { runId: string; traceIds: string[] }) =>
        MLflowService.linkTracesToRunApiMlflowTracesLinkToRunPost(params),
      linkTracesToSession: (params: { reviewAppId: string; sessionId: string; mlflow_run_id: string; trace_ids: string[] }) =>
        ApiService.linkTracesToSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdLinkTracesPost(
          params.reviewAppId, params.sessionId, { mlflow_run_id: params.mlflow_run_id, trace_ids: params.trace_ids }
        ),
      getExperiment: (params: { experimentId: string }) =>
        MLflowService.getExperimentApiMlflowExperimentsExperimentIdGet(params.experimentId),
      getRun: (params: { runId: string }) =>
        MLflowService.getRunApiMlflowRunsRunIdGet(params.runId),
      createRun: (params: any) =>
        MLflowService.createRunApiMlflowRunsPost(params),
      updateRun: (params: any) =>
        MLflowService.updateRunApiMlflowRunsUpdatePost(params),
      
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
            model_endpoint: params.model_endpoint ?? 'databricks-claude-sonnet-4',
          }
        ),
    };
  }
}

// Export a singleton instance
export const apiClient = new ApiClientWrapper();
