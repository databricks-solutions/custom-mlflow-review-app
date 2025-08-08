/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to update existing feedback on a trace.
 */
export type UpdateFeedbackRequest = {
    assessment_id: string;
    feedback_value: (string | number | boolean);
    rationale?: (string | null);
};

