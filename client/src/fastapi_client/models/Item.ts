/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatRound } from './ChatRound';
import type { DatasetSource } from './DatasetSource';
import type { ItemState } from './ItemState';
import type { LabelValue } from './LabelValue';
import type { TraceSource } from './TraceSource';
/**
 * Labeling session item.
 */
export type Item = {
    item_id?: (string | null);
    create_time?: (string | null);
    created_by?: (string | null);
    last_update_time?: (string | null);
    last_updated_by?: (string | null);
    source?: (TraceSource | DatasetSource | null);
    state?: (ItemState | null);
    chat_rounds?: (Array<ChatRound> | null);
    labels?: (Record<string, LabelValue> | null);
    /**
     * Preview of the request content
     */
    request_preview?: (string | null);
    /**
     * Preview of the response content
     */
    response_preview?: (string | null);
};

