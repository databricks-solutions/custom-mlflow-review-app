/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Labeling schema configuration.
 */
export type LabelingSchema = {
  name: string;
  type: "FEEDBACK" | "EXPECTATION";
  title: string;
  instruction?: string | null;
  enable_comment?: boolean | null;
  categorical?: Record<string, Array<string>> | null;
  categorical_list?: Record<string, Array<string>> | null;
  text?: Record<string, number> | null;
  text_list?: Record<string, any> | null;
  numeric?: Record<string, number> | null;
};
