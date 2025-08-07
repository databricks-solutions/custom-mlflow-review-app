/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { server__routers__core__experiment_summary__AnalysisStatus } from '../models/server__routers__core__experiment_summary__AnalysisStatus';
import type { server__routers__core__experiment_summary__TriggerAnalysisRequest } from '../models/server__routers__core__experiment_summary__TriggerAnalysisRequest';
import type { UserInfo } from '../models/UserInfo';
import type { UserWorkspaceInfo } from '../models/UserWorkspaceInfo';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CoreService {
    /**
     * Get Current User Role
     * Get the current user's role and permissions.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCurrentUserRoleApiAuthUserRoleGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/auth/user-role',
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
            method: 'GET',
            url: '/api/config/',
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
    public static getExperimentIdApiConfigExperimentIdGet(): CancelablePromise<Record<string, (string | null)>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/config/experiment-id',
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
            method: 'GET',
            url: '/api/user/me',
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
            method: 'GET',
            url: '/api/user/me/debug',
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
            method: 'GET',
            url: '/api/user/me/workspace',
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
     * @returns server__routers__core__experiment_summary__AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static triggerAnalysisApiExperimentSummaryTriggerAnalysisPost(
        requestBody: server__routers__core__experiment_summary__TriggerAnalysisRequest,
    ): CancelablePromise<server__routers__core__experiment_summary__AnalysisStatus> {
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
     * @returns server__routers__core__experiment_summary__AnalysisStatus Successful Response
     * @throws ApiError
     */
    public static getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet(
        experimentId: string,
    ): CancelablePromise<server__routers__core__experiment_summary__AnalysisStatus> {
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
}
