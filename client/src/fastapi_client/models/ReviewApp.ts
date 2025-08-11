/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agent } from './Agent';
import type { LabelingSchema } from './LabelingSchema';
/**
 * Review app model.
 */
export type ReviewApp = {
    review_app_id?: (string | null);
    experiment_id: string;
    agents?: (Array<Agent> | null);
    labeling_schemas?: (Array<LabelingSchema> | null);
};

