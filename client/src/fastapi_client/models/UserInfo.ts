/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Databricks user information with authentication details and role.
 */
export type UserInfo = {
    userName: string;
    displayName?: (string | null);
    active: boolean;
    emails?: Array<string>;
    is_obo?: boolean;
    has_token?: boolean;
    role?: string;
    is_developer?: boolean;
    can_access_dev_pages?: boolean;
};

