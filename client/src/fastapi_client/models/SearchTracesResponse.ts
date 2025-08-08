/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Trace } from "./Trace";
/**
 * Response model for search traces.
 */
export type SearchTracesResponse = {
  traces: Array<Trace>;
  next_page_token?: string | null;
};
