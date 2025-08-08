/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to trigger AI analysis of an experiment.
 */
export type server__routers__core__experiment_summary__TriggerAnalysisRequest = {
  experiment_id: string;
  focus?: string;
  trace_sample_size?: number;
  model_endpoint?: string;
};
