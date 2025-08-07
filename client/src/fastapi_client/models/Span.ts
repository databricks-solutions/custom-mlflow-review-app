/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SpanStatus } from './SpanStatus';
/**
 * A single span within a trace.
 */
export type Span = {
    name: string;
    span_id: string;
    parent_id?: (string | null);
    start_time_ms: number;
    end_time_ms: number;
    status: SpanStatus;
    span_type: string;
    inputs?: null;
    outputs?: null;
    attributes?: (Record<string, any> | null);
};

