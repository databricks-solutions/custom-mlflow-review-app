/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Item } from '../models/Item';
import type { ListItemsResponse } from '../models/ListItemsResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LabelingItemsService {
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
        filter?: (string | null),
        pageSize: number = 500,
        pageToken?: (string | null),
    ): CancelablePromise<ListItemsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items',
            path: {
                'review_app_id': reviewAppId,
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
     * @param reviewAppId
     * @param labelingSessionId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static batchCreateItemsApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsBatchCreatePost(
        reviewAppId: string,
        labelingSessionId: string,
        requestBody: Record<string, any>,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/batchCreate',
            path: {
                'review_app_id': reviewAppId,
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
     * @param reviewAppId
     * @param labelingSessionId
     * @param itemId
     * @returns Item Successful Response
     * @throws ApiError
     */
    public static getItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdGet(
        reviewAppId: string,
        labelingSessionId: string,
        itemId: string,
    ): CancelablePromise<Item> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'review_app_id': reviewAppId,
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
        requestBody: Item,
    ): CancelablePromise<Item> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'review_app_id': reviewAppId,
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
     * @param reviewAppId
     * @param labelingSessionId
     * @param itemId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteItemApiReviewAppsReviewAppIdLabelingSessionsLabelingSessionIdItemsItemIdDelete(
        reviewAppId: string,
        labelingSessionId: string,
        itemId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/review-apps/{review_app_id}/labeling-sessions/{labeling_session_id}/items/{item_id}',
            path: {
                'review_app_id': reviewAppId,
                'labeling_session_id': labelingSessionId,
                'item_id': itemId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
