/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response from linking traces to a labeling session.
 */
export type LinkTracesToSessionResponse = {
    success: boolean;
    linked_traces: number;
    message?: (string | null);
    items_created?: (number | null);
};

