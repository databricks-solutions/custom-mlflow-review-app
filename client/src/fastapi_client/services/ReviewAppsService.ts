/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Item } from '../models/Item';
import type { LabelingSchema } from '../models/LabelingSchema';
import type { LabelingSession } from '../models/LabelingSession';
import type { LinkTracesToSessionRequest } from '../models/LinkTracesToSessionRequest';
import type { LinkTracesToSessionResponse } from '../models/LinkTracesToSessionResponse';
import type { ListItemsResponse } from '../models/ListItemsResponse';
import type { ReviewApp } from '../models/ReviewApp';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReviewAppsService {
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
}
