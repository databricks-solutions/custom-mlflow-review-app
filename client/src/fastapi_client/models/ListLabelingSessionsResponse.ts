/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LabelingSession } from "./LabelingSession";
/**
 * Response for listing labeling sessions.
 */
export type ListLabelingSessionsResponse = {
  labeling_sessions: Array<LabelingSession>;
  next_page_token?: string | null;
};
