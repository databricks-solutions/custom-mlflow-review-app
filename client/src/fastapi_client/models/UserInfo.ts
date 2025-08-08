/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Databricks user information with authentication details.
 */
export type UserInfo = {
  userName: string;
  displayName?: string | null;
  active: boolean;
  emails?: Array<string>;
  is_obo?: boolean;
  has_token?: boolean;
};
