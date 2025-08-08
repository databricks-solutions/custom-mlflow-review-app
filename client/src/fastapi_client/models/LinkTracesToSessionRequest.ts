/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to link traces to a labeling session.
 */
export type LinkTracesToSessionRequest = {
  mlflow_run_id: string;
  trace_ids: Array<string>;
};
