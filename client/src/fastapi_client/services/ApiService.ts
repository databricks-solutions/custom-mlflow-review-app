/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalysisStatus } from '../models/AnalysisStatus';
import type { AppManifest } from '../models/AppManifest';
import type { CreateRunRequest } from '../models/CreateRunRequest';
import type { Item } from '../models/Item';
import type { LabelingSchema } from '../models/LabelingSchema';
import type { LabelingSession } from '../models/LabelingSession';
import type { LinkTracesResponse } from '../models/LinkTracesResponse';
import type { LinkTracesToRunRequest } from '../models/LinkTracesToRunRequest';
import type { LinkTracesToSessionRequest } from '../models/LinkTracesToSessionRequest';
import type { LinkTracesToSessionResponse } from '../models/LinkTracesToSessionResponse';
import type { ListItemsResponse } from '../models/ListItemsResponse';
import type { LogExpectationRequest } from '../models/LogExpectationRequest';
import type { LogExpectationResponse } from '../models/LogExpectationResponse';
import type { LogFeedbackRequest } from '../models/LogFeedbackRequest';
import type { LogFeedbackResponse } from '../models/LogFeedbackResponse';
import type { ReviewApp } from '../models/ReviewApp';
import type { SearchRunsRequest } from '../models/SearchRunsRequest';
import type { SearchRunsResponse } from '../models/SearchRunsResponse';
import type { SearchTracesRequest } from '../models/SearchTracesRequest';
import type { TraceAnalysisResponse } from '../models/TraceAnalysisResponse';
import type { TriggerAnalysisRequest } from '../models/TriggerAnalysisRequest';
import type { UpdateExpectationRequest } from '../models/UpdateExpectationRequest';
import type { UpdateExpectationResponse } from '../models/UpdateExpectationResponse';
import type { UpdateFeedbackRequest } from '../models/UpdateFeedbackRequest';
import type { UpdateFeedbackResponse } from '../models/UpdateFeedbackResponse';
import type { UpdateRunRequest } from '../models/UpdateRunRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ApiService {
    /**
     * Get App Manifest
     * Get complete application manifest including user, workspace, and config.
     *
     * Optimized to run independent API calls in parallel for better performance.
     * @returns AppManifest Successful Response
     * @throws ApiError
     */
    public static getAppManifestApiManifestGet(): CancelablePromise<AppManifest> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/manifest',
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
            method: 'GET',
            url: '/api/auth/check-dev-access',
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
        experimentId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/experiment-summary/{experiment_id}',
            path: {
                'experiment_id': experimentId,
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
     * @returns AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static triggerAnalysisApiExperimentSummaryTriggerAnalysisPost(
        requestBody: TriggerAnalysisRequest,
    ): CancelablePromise<AnalysisStatus> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/experiment-summary/trigger-analysis',
            body: requestBody,
            mediaType: 'application/json',
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
     * @returns AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet(
        experimentId: string,
    ): CancelablePromise<AnalysisStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/experiment-summary/status/{experiment_id}',
            path: {
                'experiment_id': experimentId,
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
     * @returns any Successful Response
     * @throws ApiError
     */
    public static searchTracesApiMlflowSearchTracesPost(
        requestBody: SearchTracesRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/search-traces',
            body: requestBody,
            mediaType: 'application/json',
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
    public static getRunApiMlflowRunsRunIdGet(
        runId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/runs/{run_id}',
            path: {
                'run_id': runId,
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
        requestBody: CreateRunRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/runs/create',
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: UpdateRunRequest,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/runs/update',
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: SearchRunsRequest,
    ): CancelablePromise<SearchRunsResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/runs/search',
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: LinkTracesToRunRequest,
    ): CancelablePromise<LinkTracesResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/traces/link-to-run',
            body: requestBody,
            mediaType: 'application/json',
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
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTraceApiMlflowTracesTraceIdGet(
        traceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/traces/{trace_id}',
            path: {
                'trace_id': traceId,
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
        traceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/traces/{trace_id}/data',
            path: {
                'trace_id': traceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Trace Metadata
     * Get trace metadata (info and spans without heavy inputs/outputs).
     *
     * Note: This endpoint is currently unused in the UI but kept for API compatibility.
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getTraceMetadataApiMlflowTracesTraceIdMetadataGet(
        traceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/traces/{trace_id}/metadata',
            path: {
                'trace_id': traceId,
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
        requestBody: LogFeedbackRequest,
    ): CancelablePromise<LogFeedbackResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/traces/{trace_id}/feedback',
            path: {
                'trace_id': traceId,
            },
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: UpdateFeedbackRequest,
    ): CancelablePromise<UpdateFeedbackResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/mlflow/traces/{trace_id}/feedback',
            path: {
                'trace_id': traceId,
            },
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: LogExpectationRequest,
    ): CancelablePromise<LogExpectationResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/mlflow/traces/{trace_id}/expectation',
            path: {
                'trace_id': traceId,
            },
            body: requestBody,
            mediaType: 'application/json',
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
        requestBody: UpdateExpectationRequest,
    ): CancelablePromise<UpdateExpectationResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/mlflow/traces/{trace_id}/expectation',
            path: {
                'trace_id': traceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
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
        reviewAppId: string,
    ): CancelablePromise<ReviewApp> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/review-apps/{review_app_id}',
            path: {
                'review_app_id': reviewAppId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Label Schemas
     * List all label schemas for the cached review app.
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static listLabelSchemasApiLabelSchemasGet(): CancelablePromise<Array<LabelingSchema>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/label-schemas',
        });
    }
    /**
     * Create Label Schema
     * Create a new label schema in the cached review app.
     * @param requestBody
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static createLabelSchemaApiLabelSchemasPost(
        requestBody: LabelingSchema,
    ): CancelablePromise<LabelingSchema> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/label-schemas',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Label Schema
     * Delete a label schema from the cached review app.
     * @param schemaName
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteLabelSchemaApiLabelSchemasSchemaNameDelete(
        schemaName: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/label-schemas/{schema_name}',
            path: {
                'schema_name': schemaName,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Label Schema
     * Update an existing label schema in the cached review app.
     * @param schemaName
     * @param requestBody
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static updateLabelSchemaApiLabelSchemasSchemaNamePatch(
        schemaName: string,
        requestBody: LabelingSchema,
    ): CancelablePromise<LabelingSchema> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/label-schemas/{schema_name}',
            path: {
                'schema_name': schemaName,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Labeling Sessions
     * List labeling sessions for the cached review app.
     *
     * Developers see all sessions, SMEs only see sessions they're assigned to.
     *
     * Common filters:
     * - state=IN_PROGRESS
     * - assigned_users=user@example.com
     * @param filter Filter string
     * @param pageSize
     * @param pageToken
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listLabelingSessionsApiLabelingSessionsGet(
        filter?: (string | null),
        pageSize: number = 500,
        pageToken?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions',
            query: {
                'filter': filter,
                'page_size': pageSize,
                'page_token': pageToken,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Labeling Session
     * Create a new labeling session for the cached review app. Requires developer role.
     * @param requestBody
     * @returns LabelingSession Successful Response
     * @throws ApiError
     */
    public static createLabelingSessionApiLabelingSessionsPost(
        requestBody: LabelingSession,
    ): CancelablePromise<LabelingSession> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/labeling-sessions',
            body: requestBody,
            mediaType: 'application/json',
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
     * @param labelingSessionId
     * @returns LabelingSession Successful Response
     * @throws ApiError
     */
    public static getLabelingSessionApiLabelingSessionsLabelingSessionIdGet(
        labelingSessionId: string,
    ): CancelablePromise<LabelingSession> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions/{labeling_session_id}',
            path: {
                'labeling_session_id': labelingSessionId,
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
     * @param labelingSessionId
     * @param updateMask Comma-separated list of fields to update
     * @param requestBody
     * @returns LabelingSession Successful Response
     * @throws ApiError
     */
    public static updateLabelingSessionApiLabelingSessionsLabelingSessionIdPatch(
        labelingSessionId: string,
        updateMask: string,
        requestBody: LabelingSession,
    ): CancelablePromise<LabelingSession> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/labeling-sessions/{labeling_session_id}',
            path: {
                'labeling_session_id': labelingSessionId,
            },
            query: {
                'update_mask': updateMask,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Labeling Session
     * Delete a labeling session. Requires developer role.
     * @param labelingSessionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteLabelingSessionApiLabelingSessionsLabelingSessionIdDelete(
        labelingSessionId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/labeling-sessions/{labeling_session_id}',
            path: {
                'labeling_session_id': labelingSessionId,
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
     * @param labelingSessionId
     * @param requestBody
     * @returns LinkTracesToSessionResponse Successful Response
     * @throws ApiError
     */
    public static linkTracesToSessionApiLabelingSessionsLabelingSessionIdLinkTracesPost(
        labelingSessionId: string,
        requestBody: LinkTracesToSessionRequest,
    ): CancelablePromise<LinkTracesToSessionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/labeling-sessions/{labeling_session_id}/link-traces',
            path: {
                'labeling_session_id': labelingSessionId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Items
     * List items in a labeling session.
     *
     * Returns only item state data without trace content.
     * UI should fetch trace data separately via /search-traces endpoint.
     * @param labelingSessionId
     * @param filter Filter string (e.g., state=PENDING)
     * @param pageSize
     * @param pageToken
     * @returns ListItemsResponse Successful Response
     * @throws ApiError
     */
    public static listItemsApiLabelingSessionsLabelingSessionIdItemsGet(
        labelingSessionId: string,
        filter?: (string | null),
        pageSize: number = 500,
        pageToken?: (string | null),
    ): CancelablePromise<ListItemsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions/{labeling_session_id}/items',
            path: {
                'labeling_session_id': labelingSessionId,
            },
            query: {
                'filter': filter,
                'page_size': pageSize,
                'page_token': pageToken,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Batch Create Items
     * Batch create items by proxying to Databricks API.
     * @param labelingSessionId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchCreateItemsApiLabelingSessionsLabelingSessionIdItemsBatchCreatePost(
        labelingSessionId: string,
        requestBody: Record<string, any>,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/labeling-sessions/{labeling_session_id}/items/batchCreate',
            path: {
                'labeling_session_id': labelingSessionId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Item
     * Get a specific item.
     * @param labelingSessionId
     * @param itemId
     * @returns Item Successful Response
     * @throws ApiError
     */
    public static getItemApiLabelingSessionsLabelingSessionIdItemsItemIdGet(
        labelingSessionId: string,
        itemId: string,
    ): CancelablePromise<Item> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'labeling_session_id': labelingSessionId,
                'item_id': itemId,
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
     * @param labelingSessionId
     * @param itemId
     * @param updateMask Comma-separated list of fields to update
     * @param requestBody
     * @returns Item Successful Response
     * @throws ApiError
     */
    public static updateItemApiLabelingSessionsLabelingSessionIdItemsItemIdPatch(
        labelingSessionId: string,
        itemId: string,
        updateMask: string,
        requestBody: Item,
    ): CancelablePromise<Item> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'labeling_session_id': labelingSessionId,
                'item_id': itemId,
            },
            query: {
                'update_mask': updateMask,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Item
     * Delete/unlink an item from the labeling session.
     * @param labelingSessionId
     * @param itemId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteItemApiLabelingSessionsLabelingSessionIdItemsItemIdDelete(
        labelingSessionId: string,
        itemId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'labeling_session_id': labelingSessionId,
                'item_id': itemId,
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
        experimentId?: (string | null),
    ): CancelablePromise<TraceAnalysisResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/traces/analyze-patterns',
            query: {
                'limit': limit,
                'experiment_id': experimentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
