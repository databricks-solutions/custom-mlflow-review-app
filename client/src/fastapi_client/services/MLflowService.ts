/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateRunRequest } from '../models/CreateRunRequest';
import type { GetExperimentResponse } from '../models/GetExperimentResponse';
import type { LinkTracesResponse } from '../models/LinkTracesResponse';
import type { LinkTracesToRunRequest } from '../models/LinkTracesToRunRequest';
import type { LogExpectationRequest } from '../models/LogExpectationRequest';
import type { LogExpectationResponse } from '../models/LogExpectationResponse';
import type { LogFeedbackRequest } from '../models/LogFeedbackRequest';
import type { LogFeedbackResponse } from '../models/LogFeedbackResponse';
import type { SearchRunsRequest } from '../models/SearchRunsRequest';
import type { SearchRunsResponse } from '../models/SearchRunsResponse';
import type { SearchTracesRequest } from '../models/SearchTracesRequest';
import type { SearchTracesResponse } from '../models/SearchTracesResponse';
import type { Trace } from '../models/Trace';
import type { UpdateRunRequest } from '../models/UpdateRunRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MLflowService {
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
        requestBody: SearchTracesRequest,
    ): CancelablePromise<SearchTracesResponse> {
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
     * Get Experiment
     * Get experiment details by ID.
     * @param experimentId
     * @returns GetExperimentResponse Successful Response
     * @throws ApiError
     */
    public static getExperimentApiMlflowExperimentsExperimentIdGet(
        experimentId: string,
    ): CancelablePromise<GetExperimentResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/experiments/{experiment_id}',
            path: {
                'experiment_id': experimentId,
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
     * run_id: Optional run ID to help locate the trace
     * @param traceId
     * @param runId
     * @returns Trace Successful Response
     * @throws ApiError
     */
    public static getTraceApiMlflowTracesTraceIdGet(
        traceId: string,
        runId?: string,
    ): CancelablePromise<Trace> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/mlflow/traces/{trace_id}',
            path: {
                'trace_id': traceId,
            },
            query: {
                'run_id': runId,
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
}
