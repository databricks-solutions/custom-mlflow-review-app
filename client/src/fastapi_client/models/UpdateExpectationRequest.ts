/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to update existing expectation on a trace.
 */
export type UpdateExpectationRequest = {
  assessment_id: string;
  expectation_value: string | number | boolean | Record<string, any>;
  rationale?: string | null;
};
