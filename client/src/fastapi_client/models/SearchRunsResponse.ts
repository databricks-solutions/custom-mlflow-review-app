/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MLflowRunInfo } from "./MLflowRunInfo";
/**
 * Response from searching runs.
 */
export type SearchRunsResponse = {
  runs: Array<MLflowRunInfo>;
  next_page_token?: string | null;
};
