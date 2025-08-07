/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to log expectation on a trace.
 */
export type LogExpectationRequest = {
    expectation_key: string;
    expectation_value: (string | number | boolean | Record<string, any>);
    expectation_comment?: (string | null);
};

