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
}
