/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentConfig } from './AgentConfig';
import type { DatasetConfig } from './DatasetConfig';
import type { LabelingSchemaRef } from './LabelingSchemaRef';
/**
 * Labeling session model.
 */
export type LabelingSession = {
    labeling_session_id?: (string | null);
    mlflow_run_id?: (string | null);
    create_time?: (string | null);
    created_by?: (string | null);
    last_update_time?: (string | null);
    last_updated_by?: (string | null);
    name: string;
    assigned_users?: (Array<string> | null);
    agent?: (AgentConfig | null);
    labeling_schemas?: (Array<LabelingSchemaRef> | null);
    dataset?: (DatasetConfig | null);
    additional_configs?: (Record<string, any> | null);
};

