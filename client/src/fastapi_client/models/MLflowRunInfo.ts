/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * MLflow run information.
 */
export type MLflowRunInfo = {
  run_id: string;
  run_uuid: string;
  experiment_id: string;
  user_id: string;
  status: string;
  start_time: number;
  end_time: number | null;
  artifact_uri: string;
  lifecycle_stage: string;
};
