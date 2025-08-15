/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AppManifest } from '../models/AppManifest';
import type { server__routers__core__experiment_summary__AnalysisStatus } from '../models/server__routers__core__experiment_summary__AnalysisStatus';
import type { server__routers__core__experiment_summary__TriggerAnalysisRequest } from '../models/server__routers__core__experiment_summary__TriggerAnalysisRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CoreService {
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
