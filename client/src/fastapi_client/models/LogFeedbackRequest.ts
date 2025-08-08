/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to log feedback on a trace.
 */
export type LogFeedbackRequest = {
  feedback_key: string;
  feedback_value: string | number | boolean;
  rationale?: string | null;
};
