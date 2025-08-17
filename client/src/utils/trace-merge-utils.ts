/**
 * Minimal utility for merging item state with trace content
 * Only used in dev dashboard where we need to show previews
 */

import { Item } from "@/fastapi_client";
import { LabelingItem } from "@/types/renderers";

export interface TraceInfo {
  trace_id: string;
  request_preview?: string | null;
  response_preview?: string | null;
  assessments?: any[];
}

/**
 * Merge items with traces for preview display
 * Used only in the dev dashboard table view
 */
export function mergeItemsWithTraces(items: Item[], traces: any[] | undefined): LabelingItem[] {
  if (!traces || traces.length === 0) {
    // Convert items to LabelingItem format without previews
    return items.map((item) => ({
      item_id: item.item_id || "",
      state: item.state as "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED",
      labels: item.labels,
      comment: item.comment,
      source:
        item.source && "trace_id" in item.source ? { trace_id: item.source.trace_id } : undefined,
      request_preview: undefined,
      response_preview: undefined,
    }));
  }

  // Create a map of trace_id to trace info for quick lookup
  const traceMap = new Map<string, TraceInfo>();
  for (const trace of traces) {
    if (trace?.info?.trace_id) {
      traceMap.set(trace.info.trace_id, trace.info);
    }
  }

  // Merge items with trace previews and convert to LabelingItem format
  return items.map((item) => {
    let request_preview: string | undefined;
    let response_preview: string | undefined;

    if (item.source && "trace_id" in item.source) {
      const traceInfo = traceMap.get(item.source.trace_id);
      if (traceInfo) {
        request_preview = traceInfo.request_preview || undefined;
        response_preview = traceInfo.response_preview || undefined;
      }
    }

    return {
      item_id: item.item_id || "",
      state: item.state as "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED",
      labels: item.labels,
      comment: item.comment,
      source:
        item.source && "trace_id" in item.source ? { trace_id: item.source.trace_id } : undefined,
      request_preview,
      response_preview,
    };
  });
}
