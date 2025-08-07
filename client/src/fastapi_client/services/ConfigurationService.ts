/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ConfigurationService {
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
}
