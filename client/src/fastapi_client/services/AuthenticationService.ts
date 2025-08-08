/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
export class AuthenticationService {
  /**
   * Get Current User Role
   * Get the current user's role and permissions.
   * @returns any Successful Response
   * @throws ApiError
   */
  public static getCurrentUserRoleApiAuthUserRoleGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/auth/user-role",
    });
  }
  /**
   * Check Dev Access
   * Check if current user can access /dev pages.
   * @returns any Successful Response
   * @throws ApiError
   */
  public static checkDevAccessApiAuthCheckDevAccessGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/auth/check-dev-access",
    });
  }
}
