/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request model for searching traces.
 */
export type SearchTracesRequest = {
  /**
   * List of experiment IDs to search
   */
  experiment_ids?: Array<string> | null;
  /**
   * Search filter string
   */
  filter?: string | null;
  /**
   * Run ID to filter by
   */
  run_id?: string | null;
  /**
   * Maximum number of results
   */
  max_results?: number | null;
  /**
   * Pagination token
   */
  page_token?: string | null;
  /**
   * Sort order
   */
  order_by?: Array<string> | null;
  /**
   * Whether to include span data in results
   */
  include_spans?: boolean | null;
};
