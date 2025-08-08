/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Assessment/evaluation of a trace.
 */
export type Assessment = {
  name: string;
  value: number | string | boolean | Array<string> | Record<string, any>;
  rationale?: string | null;
  metadata?: Record<string, any> | null;
  source?: string | Record<string, any> | null;
};
