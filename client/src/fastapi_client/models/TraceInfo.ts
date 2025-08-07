/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Assessment } from './Assessment';
import type { TraceLocation } from './TraceLocation';
/**
 * Trace information model.
 */
export type TraceInfo = {
    trace_id: string;
    trace_location: TraceLocation;
    request_time: string;
    execution_duration: string;
    state: string;
    trace_metadata?: (Record<string, string> | null);
    tags?: (Record<string, string> | null);
    assessments?: (Array<Assessment> | null);
    /**
     * Preview of the request content
     */
    request_preview?: (string | null);
    /**
     * Preview of the response content
     */
    response_preview?: (string | null);
};

