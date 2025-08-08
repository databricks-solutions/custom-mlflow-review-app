/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Item } from "./Item";
/**
 * Response for listing items.
 */
export type ListItemsResponse = {
  items: Array<Item>;
  next_page_token?: string | null;
};
