/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateRunRequest } from "../models/CreateRunRequest";
import type { GetExperimentResponse } from "../models/GetExperimentResponse";
import type { Item } from "../models/Item";
import type { LabelingSession } from "../models/LabelingSession";
import type { LinkTracesResponse } from "../models/LinkTracesResponse";
import type { LinkTracesToRunRequest } from "../models/LinkTracesToRunRequest";
import type { LinkTracesToSessionRequest } from "../models/LinkTracesToSessionRequest";
import type { LinkTracesToSessionResponse } from "../models/LinkTracesToSessionResponse";
import type { ListItemsResponse } from "../models/ListItemsResponse";
import type { ListLabelingSessionsResponse } from "../models/ListLabelingSessionsResponse";
import type { LogExpectationRequest } from "../models/LogExpectationRequest";
import type { LogExpectationResponse } from "../models/LogExpectationResponse";
import type { LogFeedbackRequest } from "../models/LogFeedbackRequest";
import type { LogFeedbackResponse } from "../models/LogFeedbackResponse";
import type { ReviewApp } from "../models/ReviewApp";
import type { SearchRunsRequest } from "../models/SearchRunsRequest";
import type { SearchRunsResponse } from "../models/SearchRunsResponse";
import type { SearchTracesRequest } from "../models/SearchTracesRequest";
import type { SearchTracesResponse } from "../models/SearchTracesResponse";
import type { server__routers__core__experiment_summary__AnalysisStatus } from "../models/server__routers__core__experiment_summary__AnalysisStatus";
import type { server__routers__core__experiment_summary__TriggerAnalysisRequest } from "../models/server__routers__core__experiment_summary__TriggerAnalysisRequest";
import type { server__routers__review__labeling_sessions__AnalysisStatus } from "../models/server__routers__review__labeling_sessions__AnalysisStatus";
import type { server__routers__review__labeling_sessions__TriggerAnalysisRequest } from "../models/server__routers__review__labeling_sessions__TriggerAnalysisRequest";
import type { Trace } from "../models/Trace";
import type { TraceAnalysisResponse } from "../models/TraceAnalysisResponse";
import type { UpdateExpectationRequest } from "../models/UpdateExpectationRequest";
import type { UpdateExpectationResponse } from "../models/UpdateExpectationResponse";
import type { UpdateFeedbackRequest } from "../models/UpdateFeedbackRequest";
import type { UpdateFeedbackResponse } from "../models/UpdateFeedbackResponse";
import type { UpdateRunRequest } from "../models/UpdateRunRequest";
import type { UserInfo } from "../models/UserInfo";
import type { UserWorkspaceInfo } from "../models/UserWorkspaceInfo";
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
export class ApiService {
  /**
   * Get Current User Role
   * Get the current user's role and permissions.
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getCurrentUserRoleApiAuthUserRoleGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/auth/user-role",
    });
  }
  /**
   * Check Dev Access
   * Check if current user can access /dev pages.
   * @returns any Successful Response
   * @throws ApiError
   */
  public static checkDevAccessApiAuthCheckDevAccessGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/auth/check-dev-access",
    });
  }
  /**
   * Get Config
   * Get application configuration.
   *
   * Returns:
   * Dictionary containing public configuration values
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getConfigApiConfigGet(): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/",
    });
  }
  /**
   * Get Experiment Id
   * Get the primary experiment ID.
   *
   * Returns:
   * Dictionary containing the experiment ID
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getExperimentIdApiConfigExperimentIdGet(): CancelablePromise<
    Record<string, string | null>
  > {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/config/experiment-id",
    });
  }
  /**
   * Get Current User
   * Get current user information from Databricks with auth details.
   * @returns UserInfo Successful Response
   * @throws ApiError
   */
  public static getCurrentUserApiUserMeGet(): CancelablePromise<UserInfo> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/user/me",
    });
  }
  /**
   * Debug Auth
   * Debug endpoint to see auth middleware state.
   * @returns any Successful Response
   * @throws ApiError
   */
  public static debugAuthApiUserMeDebugGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/user/me/debug",
    });
  }
  /**
   * Get User Workspace Info
   * Get user information along with workspace details.
   * @returns UserWorkspaceInfo Successful Response
   * @throws ApiError
   */
  public static getUserWorkspaceInfoApiUserMeWorkspaceGet(): CancelablePromise<UserWorkspaceInfo> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/user/me/workspace",
    });
  }
  /**
   * Get Experiment Summary
   * Get experiment summary from MLflow artifacts.
   *
   * Args:
   * experiment_id: The MLflow experiment ID
   *
   * Returns:
   * Dictionary containing summary content and metadata
   * @param experimentId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getExperimentSummaryApiExperimentSummaryExperimentIdGet(
    experimentId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/experiment-summary/{experiment_id}",
      path: {
        experiment_id: experimentId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Trigger Analysis
   * Trigger AI analysis for an experiment.
   *
   * This runs the analysis in the background and returns immediately.
   *
   * Args:
   * request: Analysis request parameters
   *
   * Returns:
   * Status of the analysis request
   * @param requestBody
   * @returns server__routers__core__experiment_summary__AnalysisStatus Successful Response
   * @throws ApiError
   */
  public static triggerAnalysisApiExperimentSummaryTriggerAnalysisPost(
    requestBody: server__routers__core__experiment_summary__TriggerAnalysisRequest
  ): CancelablePromise<server__routers__core__experiment_summary__AnalysisStatus> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/experiment-summary/trigger-analysis",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Analysis Status
   * Get the status of an analysis request.
   *
   * Args:
   * experiment_id: The experiment ID
   *
   * Returns:
   * Current status of the analysis
   * @param experimentId
   * @returns server__routers__core__experiment_summary__AnalysisStatus Successful Response
   * @throws ApiError
   */
  public static getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet(
    experimentId: string
  ): CancelablePromise<server__routers__core__experiment_summary__AnalysisStatus> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/experiment-summary/status/{experiment_id}",
      path: {
        experiment_id: experimentId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Search Traces
   * Search for traces in MLflow experiments.
   *
   * Uses MLflow SDK since there's no direct API endpoint.
   * @param requestBody
   * @returns SearchTracesResponse Successful Response
   * @throws ApiError
   */
  public static searchTracesApiMlflowSearchTracesPost(
    requestBody: SearchTracesRequest
  ): CancelablePromise<SearchTracesResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/search-traces",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Experiment
   * Get experiment details by ID.
   * @param experimentId
   * @returns GetExperimentResponse Successful Response
   * @throws ApiError
   */
  public static getExperimentApiMlflowExperimentsExperimentIdGet(
    experimentId: string
  ): CancelablePromise<GetExperimentResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/mlflow/experiments/{experiment_id}",
      path: {
        experiment_id: experimentId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Run
   * Get run details by ID.
   * @param runId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getRunApiMlflowRunsRunIdGet(runId: string): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/mlflow/runs/{run_id}",
      path: {
        run_id: runId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Create Run
   * Create a new MLflow run.
   * @param requestBody
   * @returns any Successful Response
   * @throws ApiError
   */
  public static createRunApiMlflowRunsCreatePost(
    requestBody: CreateRunRequest
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/runs/create",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update Run
   * Update an MLflow run.
   * @param requestBody
   * @returns string Successful Response
   * @throws ApiError
   */
  public static updateRunApiMlflowRunsUpdatePost(
    requestBody: UpdateRunRequest
  ): CancelablePromise<Record<string, string>> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/runs/update",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Search Runs
   * Search for runs in experiments.
   * @param requestBody
   * @returns SearchRunsResponse Successful Response
   * @throws ApiError
   */
  public static searchRunsApiMlflowRunsSearchPost(
    requestBody: SearchRunsRequest
  ): CancelablePromise<SearchRunsResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/runs/search",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Link Traces To Run
   * Link traces to an MLflow run.
   *
   * Note: For labeling sessions, use the combined endpoint at:
   * POST /api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/link-traces
   *
   * This endpoint only handles MLflow trace linking, not labeling session item creation.
   * @param requestBody
   * @returns LinkTracesResponse Successful Response
   * @throws ApiError
   */
  public static linkTracesToRunApiMlflowTracesLinkToRunPost(
    requestBody: LinkTracesToRunRequest
  ): CancelablePromise<LinkTracesResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/traces/link-to-run",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Trace
   * Get trace information by ID.
   *
   * Args:
   * trace_id: The trace ID
   * run_id: Optional run ID to help locate the trace
   * @param traceId
   * @param runId
   * @returns Trace Successful Response
   * @throws ApiError
   */
  public static getTraceApiMlflowTracesTraceIdGet(
    traceId: string,
    runId?: string
  ): CancelablePromise<Trace> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/mlflow/traces/{trace_id}",
      path: {
        trace_id: traceId,
      },
      query: {
        run_id: runId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Trace Data
   * Get trace data (spans) by trace ID.
   * @param traceId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getTraceDataApiMlflowTracesTraceIdDataGet(
    traceId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/mlflow/traces/{trace_id}/data",
      path: {
        trace_id: traceId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Trace Metadata
   * Get trace metadata (info and spans without heavy inputs/outputs).
   * @param traceId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getTraceMetadataApiMlflowTracesTraceIdMetadataGet(
    traceId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/mlflow/traces/{trace_id}/metadata",
      path: {
        trace_id: traceId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Log Trace Feedback
   * Log feedback on a trace.
   *
   * Args:
   * trace_id: The trace ID to log feedback for
   * request: The feedback request containing key, value, and optional comment
   *
   * Returns:
   * LogFeedbackResponse indicating success or failure
   * @param traceId
   * @param requestBody
   * @returns LogFeedbackResponse Successful Response
   * @throws ApiError
   */
  public static logTraceFeedbackApiMlflowTracesTraceIdFeedbackPost(
    traceId: string,
    requestBody: LogFeedbackRequest
  ): CancelablePromise<LogFeedbackResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/traces/{trace_id}/feedback",
      path: {
        trace_id: traceId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update Trace Feedback
   * Update existing feedback on a trace.
   *
   * Args:
   * trace_id: The trace ID to update feedback for
   * request: The update request containing assessment_id, value, and optional rationale
   *
   * Returns:
   * UpdateFeedbackResponse indicating success or failure
   * @param traceId
   * @param requestBody
   * @returns UpdateFeedbackResponse Successful Response
   * @throws ApiError
   */
  public static updateTraceFeedbackApiMlflowTracesTraceIdFeedbackPatch(
    traceId: string,
    requestBody: UpdateFeedbackRequest
  ): CancelablePromise<UpdateFeedbackResponse> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/mlflow/traces/{trace_id}/feedback",
      path: {
        trace_id: traceId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Log Trace Expectation
   * Log expectation on a trace.
   *
   * Args:
   * trace_id: The trace ID to log expectation for
   * request: The expectation request containing key, value, and optional comment
   *
   * Returns:
   * LogExpectationResponse indicating success or failure
   * @param traceId
   * @param requestBody
   * @returns LogExpectationResponse Successful Response
   * @throws ApiError
   */
  public static logTraceExpectationApiMlflowTracesTraceIdExpectationPost(
    traceId: string,
    requestBody: LogExpectationRequest
  ): CancelablePromise<LogExpectationResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/mlflow/traces/{trace_id}/expectation",
      path: {
        trace_id: traceId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update Trace Expectation
   * Update existing expectation on a trace.
   *
   * Args:
   * trace_id: The trace ID to update expectation for
   * request: The update request containing assessment_id, value, and optional rationale
   *
   * Returns:
   * UpdateExpectationResponse indicating success or failure
   * @param traceId
   * @param requestBody
   * @returns UpdateExpectationResponse Successful Response
   * @throws ApiError
   */
  public static updateTraceExpectationApiMlflowTracesTraceIdExpectationPatch(
    traceId: string,
    requestBody: UpdateExpectationRequest
  ): CancelablePromise<UpdateExpectationResponse> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/mlflow/traces/{trace_id}/expectation",
      path: {
        trace_id: traceId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Current Review App
   * Get THE review app for the configured experiment (cached server-side).
   * @returns ReviewApp Successful Response
   * @throws ApiError
   */
  public static getCurrentReviewAppApiReviewAppsCurrentGet(): CancelablePromise<ReviewApp> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/current",
    });
  }
  /**
   * Get Review App
   * Get a specific review app by ID.
   * @param reviewAppId
   * @returns ReviewApp Successful Response
   * @throws ApiError
   */
  public static getReviewAppApiReviewAppsReviewAppIdGet(
    reviewAppId: string
  ): CancelablePromise<ReviewApp> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}",
      path: {
        review_app_id: reviewAppId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * List Labeling Sessions
   * List labeling sessions for a review app.
   *
   * Developers see all sessions, SMEs only see sessions they're assigned to.
   *
   * Common filters:
   * - state=IN_PROGRESS
   * - assigned_users=user@example.com
   * @param reviewAppId
   * @param filter Filter string
   * @param pageSize
   * @param pageToken
   * @returns ListLabelingSessionsResponse Successful Response
   * @throws ApiError
   */
  public static listLabelingSessionsApiReviewAppsReviewAppIdLabelingSessionsGet(
    reviewAppId: string,
    filter?: string | null,
    pageSize: number = 500,
    pageToken?: string | null
  ): CancelablePromise<ListLabelingSessionsResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions",
      path: {
        review_app_id: reviewAppId,
      },
      query: {
        filter: filter,
        page_size: pageSize,
        page_token: pageToken,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Create Labeling Session
   * Create a new labeling session. Requires developer role.
   * @param reviewAppId
   * @param requestBody
   * @returns LabelingSession Successful Response
   * @throws ApiError
   */
  public static createLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsPost(
    reviewAppId: string,
    requestBody: LabelingSession
  ): CancelablePromise<LabelingSession> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/review-apps/{review_app_id}/labeling-sessions",
      path: {
        review_app_id: reviewAppId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Labeling Session
   * Get a specific labeling session.
   *
   * Users can access sessions they're assigned to or if they're developers.
   * @param reviewAppId
   * @param labelingSessionId
   * @returns LabelingSession Successful Response
   * @throws ApiError
   */
  public static getLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdGet(
    reviewAppId: string,
    labelingSessionId: string
  ): CancelablePromise<LabelingSession> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update Labeling Session
   * Update a labeling session. Requires developer role.
   *
   * Example update_mask: "name,assigned_users,labeling_schemas"
   * @param reviewAppId
   * @param labelingSessionId
   * @param updateMask Comma-separated list of fields to update
   * @param requestBody
   * @returns LabelingSession Successful Response
   * @throws ApiError
   */
  public static updateLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdPatch(
    reviewAppId: string,
    labelingSessionId: string,
    updateMask: string,
    requestBody: LabelingSession
  ): CancelablePromise<LabelingSession> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      query: {
        update_mask: updateMask,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Delete Labeling Session
   * Delete a labeling session. Requires developer role.
   * @param reviewAppId
   * @param labelingSessionId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static deleteLabelingSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdDelete(
    reviewAppId: string,
    labelingSessionId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Link Traces To Session
   * Link traces to a labeling session. Requires developer role.
   *
   * This endpoint combines two operations:
   * 1. Links traces to the MLflow run associated with the labeling session
   * 2. Creates labeling items for the traces in the session
   *
   * This ensures traces are properly linked for both MLflow tracking and labeling workflows.
   * @param reviewAppId
   * @param labelingSessionId
   * @param requestBody
   * @returns LinkTracesToSessionResponse Successful Response
   * @throws ApiError
   */
  public static linkTracesToSessionApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdLinkTracesPost(
    reviewAppId: string,
    labelingSessionId: string,
    requestBody: LinkTracesToSessionRequest
  ): CancelablePromise<LinkTracesToSessionResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/link-traces",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Session Analysis
   * Retrieve analysis report for a labeling session from MLflow artifacts.
   *
   * Returns the analysis if it exists, or indicates that analysis needs to be run.
   * @param reviewAppId
   * @param labelingSessionId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getSessionAnalysisApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisGet(
    reviewAppId: string,
    labelingSessionId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/analysis",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Trigger Session Analysis
   * Trigger analysis of a labeling session.
   *
   * This runs the analysis in the background and returns immediately.
   * The analysis will be stored in the session's MLflow run artifacts.
   * Re-running will overwrite the previous analysis.
   * @param reviewAppId
   * @param labelingSessionId
   * @param requestBody
   * @returns server__routers__review__labeling_sessions__AnalysisStatus Successful Response
   * @throws ApiError
   */
  public static triggerSessionAnalysisApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisTriggerPost(
    reviewAppId: string,
    labelingSessionId: string,
    requestBody: server__routers__review__labeling_sessions__TriggerAnalysisRequest
  ): CancelablePromise<server__routers__review__labeling_sessions__AnalysisStatus> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/analysis/trigger",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Analysis Status
   * Get the status of an analysis request.
   *
   * Returns the current status of the analysis (pending, running, completed, failed).
   * @param reviewAppId
   * @param labelingSessionId
   * @returns server__routers__review__labeling_sessions__AnalysisStatus Successful Response
   * @throws ApiError
   */
  public static getAnalysisStatusApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdAnalysisStatusGet(
    reviewAppId: string,
    labelingSessionId: string
  ): CancelablePromise<server__routers__review__labeling_sessions__AnalysisStatus> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/analysis/status",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * List Items
   * List items in a labeling session.
   *
   * Common filters:
   * - state=PENDING
   * - state=IN_PROGRESS
   * - state=COMPLETED
   * @param reviewAppId
   * @param labelingSessionId
   * @param filter Filter string (e.g., state=PENDING)
   * @param pageSize
   * @param pageToken
   * @returns ListItemsResponse Successful Response
   * @throws ApiError
   */
  public static listItemsApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsGet(
    reviewAppId: string,
    labelingSessionId: string,
    filter?: string | null,
    pageSize: number = 500,
    pageToken?: string | null
  ): CancelablePromise<ListItemsResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      query: {
        filter: filter,
        page_size: pageSize,
        page_token: pageToken,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Batch Create Items
   * Batch create items by proxying to Databricks API.
   * @param reviewAppId
   * @param labelingSessionId
   * @param requestBody
   * @returns any Successful Response
   * @throws ApiError
   */
  public static batchCreateItemsApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsBatchCreatePost(
    reviewAppId: string,
    labelingSessionId: string,
    requestBody: Record<string, any>
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/batchCreate",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Item
   * Get a specific item.
   * @param reviewAppId
   * @param labelingSessionId
   * @param itemId
   * @returns Item Successful Response
   * @throws ApiError
   */
  public static getItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdGet(
    reviewAppId: string,
    labelingSessionId: string,
    itemId: string
  ): CancelablePromise<Item> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
        item_id: itemId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update Item
   * Update an item.
   *
   * Example update_mask: "state,chat_rounds"
   * @param reviewAppId
   * @param labelingSessionId
   * @param itemId
   * @param updateMask Comma-separated list of fields to update
   * @param requestBody
   * @returns Item Successful Response
   * @throws ApiError
   */
  public static updateItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdPatch(
    reviewAppId: string,
    labelingSessionId: string,
    itemId: string,
    updateMask: string,
    requestBody: Item
  ): CancelablePromise<Item> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
        item_id: itemId,
      },
      query: {
        update_mask: updateMask,
      },
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Delete Item
   * Delete/unlink an item from the labeling session.
   * @param reviewAppId
   * @param labelingSessionId
   * @param itemId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static deleteItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdDelete(
    reviewAppId: string,
    labelingSessionId: string,
    itemId: string
  ): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}",
      path: {
        review_app_id: reviewAppId,
        labeling_session_id: labelingSessionId,
        item_id: itemId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
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
