/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LabelingSchema } from '../models/LabelingSchema';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LabelSchemasService {
    /**
     * List Schemas
     * List all label schemas for a review app.
     * @param reviewAppId
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static listSchemasApiReviewAppsReviewAppIdSchemasGet(
        reviewAppId: string,
    ): CancelablePromise<Array<LabelingSchema>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/review-apps/{review_app_id}/schemas',
            path: {
                'review_app_id': reviewAppId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Schema
     * Create a new label schema for a review app.
     * @param reviewAppId
     * @param requestBody
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static createSchemaApiReviewAppsReviewAppIdSchemasPost(
        reviewAppId: string,
        requestBody: LabelingSchema,
    ): CancelablePromise<LabelingSchema> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/review-apps/{review_app_id}/schemas',
            path: {
                'review_app_id': reviewAppId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Schema
     * Update an existing label schema.
     * @param reviewAppId
     * @param schemaName
     * @param requestBody
     * @returns LabelingSchema Successful Response
     * @throws ApiError
     */
    public static updateSchemaApiReviewAppsReviewAppIdSchemasSchemaNamePatch(
        reviewAppId: string,
        schemaName: string,
        requestBody: LabelingSchema,
    ): CancelablePromise<LabelingSchema> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/review-apps/{review_app_id}/schemas/{schema_name}',
            path: {
                'review_app_id': reviewAppId,
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
     * Delete Schema
     * Delete a label schema from a review app.
     * @param reviewAppId
     * @param schemaName
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteSchemaApiReviewAppsReviewAppIdSchemasSchemaNameDelete(
        reviewAppId: string,
        schemaName: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/review-apps/{review_app_id}/schemas/{schema_name}',
            path: {
                'review_app_id': reviewAppId,
                'schema_name': schemaName,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
