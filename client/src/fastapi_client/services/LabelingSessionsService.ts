/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LabelingSession } from '../models/LabelingSession';
import type { LinkTracesToSessionRequest } from '../models/LinkTracesToSessionRequest';
import type { LinkTracesToSessionResponse } from '../models/LinkTracesToSessionResponse';
import type { server__routers__review__labeling_sessions__AnalysisStatus } from '../models/server__routers__review__labeling_sessions__AnalysisStatus';
import type { server__routers__review__labeling_sessions__TriggerAnalysisRequest } from '../models/server__routers__review__labeling_sessions__TriggerAnalysisRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LabelingSessionsService {
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
     * Get Session Analysis
     * Retrieve analysis report for a labeling session from MLflow artifacts.
     *
     * Returns the analysis if it exists, or indicates that analysis needs to be run.
     * @param labelingSessionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSessionAnalysisApiLabelingSessionsLabelingSessionIdAnalysisGet(
        labelingSessionId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions/{labeling_session_id}/analysis',
            path: {
                'labeling_session_id': labelingSessionId,
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
     * @param labelingSessionId
     * @param requestBody
     * @returns server__routers__review__labeling_sessions__AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static triggerSessionAnalysisApiLabelingSessionsLabelingSessionIdAnalysisTriggerPost(
        labelingSessionId: string,
        requestBody: server__routers__review__labeling_sessions__TriggerAnalysisRequest,
    ): CancelablePromise<server__routers__review__labeling_sessions__AnalysisStatus> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/labeling-sessions/{labeling_session_id}/analysis/trigger',
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
     * Get Analysis Status
     * Get the status of an analysis request.
     *
     * Returns the current status of the analysis (pending, running, completed, failed).
     * @param labelingSessionId
     * @returns server__routers__review__labeling_sessions__AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static getAnalysisStatusApiLabelingSessionsLabelingSessionIdAnalysisStatusGet(
        labelingSessionId: string,
    ): CancelablePromise<server__routers__review__labeling_sessions__AnalysisStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/labeling-sessions/{labeling_session_id}/analysis/status',
            path: {
                'labeling_session_id': labelingSessionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
