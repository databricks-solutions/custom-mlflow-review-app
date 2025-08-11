/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Assessment/evaluation of a trace.
 */
export type Assessment = {
    assessment_id?: (string | null);
    name: string;
    value: (number | string | boolean | Array<string> | Record<string, any>);
    type?: (string | null);
    rationale?: (string | null);
    metadata?: (Record<string, any> | null);
    source?: (string | Record<string, any> | null);
};

