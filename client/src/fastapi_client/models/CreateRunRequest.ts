/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to create an MLflow run.
 */
export type CreateRunRequest = {
    experiment_id: string;
    user_id?: (string | null);
    start_time?: (number | null);
    tags?: (Record<string, string> | null);
};

