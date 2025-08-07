/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to search for MLflow runs.
 */
export type SearchRunsRequest = {
    experiment_ids: Array<string>;
    filter?: (string | null);
    run_view_type?: (string | null);
    max_results?: (number | null);
    order_by?: (Array<string> | null);
    page_token?: (string | null);
};

