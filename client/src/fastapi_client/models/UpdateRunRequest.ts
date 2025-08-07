/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to update an MLflow run.
 */
export type UpdateRunRequest = {
    run_id: string;
    status?: (string | null);
    end_time?: (number | null);
    tags?: (Array<Record<string, string>> | null);
};

