/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConfigInfo } from './ConfigInfo';
import type { ReviewApp } from './ReviewApp';
import type { UserInfo } from './UserInfo';
import type { WorkspaceInfo } from './WorkspaceInfo';
/**
 * Complete application manifest with all necessary information.
 */
export type AppManifest = {
    user: UserInfo;
    workspace: WorkspaceInfo;
    config: ConfigInfo;
    review_app?: (ReviewApp | null);
};

