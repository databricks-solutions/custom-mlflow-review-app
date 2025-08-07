import { isNil } from "lodash";

import { safex } from "@databricks/web-shared/flags";
import type {
  ModelTrace,
  ModelTraceInfo,
  ModelTraceSpan,
  NotebookModelTraceInfo,
} from "@databricks/web-shared/model-trace-explorer";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@databricks/web-shared/query-client";
import { workspaceFetch } from "@databricks/web-shared/spog/workspace-console";

import type { RunEvaluationTracesDataEntry } from "../types";

// Mirrors the REST entity here: https://src.dev.databricks.com/databricks-eng/universe@master/-/blob/managed-evals/api/proto/review_app_service.proto?L28
export interface ReviewApp {
  review_app_id?: string;
  experiment_id: string;
}

// Mirrors the REST entity here: https://src.dev.databricks.com/databricks-eng/universe@master/-/blob/managed-evals/api/proto/managed_dataset_service.proto?L39

export interface Dataset {
  dataset_id: string;
  create_time: string;
  created_by?: string;
  name?: string;
}

// Mirrors the proto here: https://src.dev.databricks.com/databricks-eng/universe@master/-/blob/managed-evals/api/proto/review_app_service.proto?L187
export interface LabelingSession {
  labeling_session_id: string;
  mlflow_run_id: string;
  name: string;
  dataset?: string;
}

async function listReviewApps(experimentId: string): Promise<ReviewApp[]> {
  let nextPageToken = undefined;
  let shouldFetch = true;

  let reviewApps: ReviewApp[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    // Create a URL from '/ajax-api/2.0/managed-evals/review-apps?filter=`${experimentId}`'
    const url = new URL(
      "/ajax-api/2.0/managed-evals/review-apps",
      window.location.origin
    );

    // Set the query params.
    url.searchParams.set("filter", `experiment_id=${experimentId}`);
    // Necessary to page fewer times.
    url.searchParams.set("page_size", "500");
    // If there is a nextPageToken, set it as a query param.
    if (nextPageToken) {
      url.searchParams.set("next_page_token", nextPageToken);
    }
    const reviewAppsResponse: {
      review_apps: ReviewApp[];
      next_page_token?: string | null;
    } = await workspaceFetch(url).then((response) => response.json());
    nextPageToken = reviewAppsResponse.next_page_token;
    if (reviewAppsResponse.review_apps) {
      reviewApps = reviewApps.concat(reviewAppsResponse.review_apps);
    }

    shouldFetch = false;
  }
  return reviewApps;
}

async function listDatasets(experimentId: string): Promise<Dataset[]> {
  let nextPageToken = undefined;
  let shouldFetch = true;

  let datasets: Dataset[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    // Create a URL from '/ajax-api/2.0/managed-evals/datasets?filter=`${experimentId}`'
    const url = new URL(
      "/ajax-api/2.0/managed-evals/datasets",
      window.location.origin
    );

    // Set the query params.
    url.searchParams.set("filter", `experiment_id=${experimentId}`);
    // Necessary to page fewer times.
    url.searchParams.set("page_size", "500");
    // If there is a nextPageToken, set it as a query param.
    if (nextPageToken) {
      url.searchParams.set("next_page_token", nextPageToken);
    }
    const datasetsResponse: {
      datasets?: Dataset[];
      next_page_token?: string | null;
    } = await workspaceFetch(url).then((response) => response.json());
    nextPageToken = datasetsResponse.next_page_token;
    if (datasetsResponse.datasets) {
      datasets = datasets.concat(datasetsResponse.datasets);
    }

    shouldFetch = false;
  }
  return datasets;
}

export function useListDatasets(experimentId: string) {
  return useQuery({
    queryKey: ["listDatasets", experimentId],
    queryFn: async (): Promise<Dataset[]> => {
      return listDatasets(experimentId);
    },
    cacheTime: 0, // Disable caching so it always refetches on page refresh
    refetchOnWindowFocus: true, // Disable refetching on window focus
    retry: false,
  });
}

export function useGetReviewApp(experimentId: string) {
  return useQuery({
    queryKey: ["getReviewApp", experimentId],
    queryFn: async (): Promise<ReviewApp | null> => {
      const reviewApps = await listReviewApps(experimentId);
      const reviewApp = reviewApps.find(
        (app) => app.experiment_id === experimentId
      );
      return reviewApp || null;
    },
    cacheTime: 0, // Disable caching so it always refetches on page refresh
    refetchOnWindowFocus: true, // When the window is focused
    retry: false,
  });
}

async function listLabelingSessions(
  reviewAppId: string
): Promise<LabelingSession[]> {
  let nextPageToken = undefined;
  let shouldFetch = true;

  let labelingSessions: LabelingSession[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    // Create a URL from '/ajax-api/2.0/managed-evals/labeling-sessions?filter=`${reviewAppId}`'
    const url = new URL(
      `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions`,
      window.location.origin
    );

    // Necessary to page fewer times.
    url.searchParams.set("page_size", "500");
    // If there is a nextPageToken, set it as a query param.
    if (nextPageToken) {
      url.searchParams.set("next_page_token", nextPageToken);
    }
    const labelingSessionsResponse: {
      labeling_sessions: LabelingSession[];
      next_page_token?: string | null;
    } = await workspaceFetch(url).then((response) => response.json());
    nextPageToken = labelingSessionsResponse.next_page_token;
    if (labelingSessionsResponse.labeling_sessions) {
      labelingSessions = labelingSessions.concat(
        labelingSessionsResponse.labeling_sessions
      );
    }

    shouldFetch = false;
  }
  return labelingSessions;
}

export function useListLabelingSessions(reviewAppId?: string) {
  return useQuery({
    queryKey: ["listLabelingSessions", reviewAppId],
    queryFn: async (): Promise<LabelingSession[]> => {
      if (!reviewAppId) {
        return [];
      }
      return listLabelingSessions(reviewAppId);
    },
    enabled: !isNil(reviewAppId),
    cacheTime: 0, // Disable caching so it always refetches on page refresh
    refetchOnWindowFocus: true, // When the window is focused
    retry: false,
  });
}

export interface GetEvalDatasetConfigurationResponse {
  version: string;
  instance_id: string;
  experiment_ids: string[];
}

export function useGetDataset(datasetId: string, datasetName: string) {
  return useQuery({
    queryKey: ["useGetDataset", datasetId],
    queryFn: () => getManagedDatasetConfiguration(datasetId, datasetName),
    staleTime: Infinity, // Keep data fresh as long as the component is mounted
    cacheTime: 0, // Disable caching so it always refetches on page refresh
    refetchOnWindowFocus: false, // Disable refetching on window focus
    retry: false,
  });
}

// Queries
const getManagedDatasetConfiguration = async (
  datasetId: string,
  datasetName: string
): Promise<GetEvalDatasetConfigurationResponse> => {
  return workspaceFetch(
    `/ajax-api/2.0/managed-evals/datasets/${datasetId}`
  ).then(async (response) => {
    const responseJson = await response.json();
    if (response.status !== 200) {
      throw new Error(
        `Failed to fetch configuration for dataset ${datasetName}. [${responseJson.error_code}]: ${responseJson.message}`
      );
    }
    return responseJson;
  });
};

// https://src.dev.databricks.com/databricks-eng/universe/-/blob/managed-evals/api/proto/managed_dataset_service.proto?L101
export interface BatchCreateDatasetRecordsRequest {
  dataset_id: string;
  requests: CreateDatasetRecordRequest[];
}

export interface BatchCreateDatasetRecordsResponse {
  dataset_records: DatasetRecord[];
}

// https://src.dev.databricks.com/databricks-eng/universe/-/blob/managed-evals/api/proto/managed_dataset_service.proto?L489:9-489:35
export interface CreateDatasetRecordRequest {
  dataset_id: string;
  dataset_record: DatasetRecord;
}

// https://src.dev.databricks.com/databricks-eng/universe/-/blob/managed-evals/api/proto/managed_dataset_service.proto?L101
export interface DatasetRecord {
  // https://src.dev.databricks.com/databricks-eng/universe@master/-/blob/rag/rag_studio/python/databricks/rag_eval/datasets/rest_entities.py?L28:7-28:13
  source: {
    trace?: {
      trace_id: string;
    };
  };
  inputs: {
    key: string;
    value: any;
  }[];
}
const batchCreateDatasetRecords = async ({
  datasetId,
  traces,
  getTrace,
}: {
  datasetId: string;
  traces: RunEvaluationTracesDataEntry[];
  getTrace: (
    requestId?: string,
    traceId?: string
  ) => Promise<ModelTrace | undefined>;
}): Promise<BatchCreateDatasetRecordsResponse> => {
  const tracePromises = traces.map((trace) =>
    getTrace(trace.requestId, trace.traceInfo?.trace_id)
  );
  const modelTraces = await Promise.all(tracePromises);

  const createDatasetRecordRequests: CreateDatasetRecordRequest[] = traces.map(
    (trace, index) => {
      const modelTrace = modelTraces[index];
      const request =
        modelTrace?.data.spans[0].attributes?.["mlflow.spanInputs"];

      let requestIsJson;
      let requestObject;
      try {
        requestObject = JSON.parse(request);
        requestIsJson = true;
      } catch (e) {
        requestIsJson = false;
      }

      let inputs;
      if (isNil(request) || requestIsJson) {
        // Convert trace.inputs (Record<string, any>) to inputs (key, value).
        inputs = Object.entries(requestObject).map(([key, value]) => {
          return {
            key,
            value,
          };
        });
      } else {
        inputs = [
          {
            key: "messages",
            value: [
              {
                role: "user",
                content: request,
              },
            ],
          },
        ];
      }

      const createRecordRequest: CreateDatasetRecordRequest = {
        dataset_id: datasetId,
        dataset_record: {
          source: {
            trace: {
              trace_id: trace.traceInfo?.trace_id || trace.requestId,
            },
          },
          inputs: inputs,
        },
      };

      return createRecordRequest;
    }
  );
  return workspaceFetch(
    `/ajax-api/2.0/managed-evals/datasets/${datasetId}/records:batchCreate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dataset_id: datasetId,
        requests: createDatasetRecordRequests,
      }),
    }
  ).then((response) => {
    return response.json();
  });
};

export interface LabelingSessionItem {
  source: {
    trace_id?: string;
  };
}
// https://src.dev.databricks.com/databricks-eng/universe/-/blob/managed-evals/api/proto/review_app_service.proto?L746
export interface BatchCreateLabelingSessionItemsRequest {
  review_app_id: string;
  labeling_session_id: string;
  items: LabelingSessionItem[];
}

export interface BatchCreateLabelingSessionItemsResponse {
  items: LabelingSessionItem[];
}

export const useBatchCreateDatasetRecordsMutation = () =>
  useMutation({
    mutationFn: batchCreateDatasetRecords,
  });

/**
 * Interfaces for the REST API to upsert traces.
 */
export type Trace = {
  trace_id: string;
  trace_location:
    | { type: "MLFLOW_EXPERIMENT"; experimentId: string }
    | { type: "INFERENCE_TABLE"; fullTableName: string };
  trace_info: TraceInfo;
  trace_data: TraceData;
};
export type TraceInfo = {
  trace_id?: string;
  timestamp_ms: number;
  // Formatted as a profobuf.Duration, e.g. "1s".
  execution_duration?: string;
  state?: "OK" | "ERROR" | "IN_PROGRESS" | "STATE_UNSPECIFIED";
  request_metadata?: Record<string, string>;
  tags?: Record<string, string>;
};
export type TraceData = {
  request?: string;
  response?: string;
  spans: ModelTraceSpan[]; // use the type from model-trace-explorer
};

export type CreateTracePayload = Omit<Trace, "trace_id">;

/**
 * Format a duration in milliseconds into a string in google.protobuf.Duration format.
 * e.g. 4311 -> "4.311s"
 */
export const formatDuration = (durationMs: number) => {
  const seconds = durationMs / 1000;
  return `${seconds}s`;
};

// Function to link traces to run (mirrors Python MLFlowClient.link_traces_to_run)
const linkTracesToRun = async (
  runId: string,
  traceIds: string[]
): Promise<void> => {
  const requestBody = {
    run_id: runId,
    trace_ids: traceIds,
  };

  const response = await workspaceFetch(
    "/ajax-api/2.0/mlflow/traces/link-to-run",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to link traces to run: ${response.status} ${response.statusText}`
    );
  }
};

const createTrace = async (
  trace: CreateTracePayload,
  sourceRunUuid?: string
): Promise<Trace> => {
  const request = {
    trace: {
      trace_info: {
        // Don't set trace_id - it's generated by the backend
        client_request_id: `client_${Date.now()}_${Math.random()
          .toString(36)
          .substr(2, 9)}`,
        trace_location: (() => {
          switch (trace.trace_location?.type) {
            case "MLFLOW_EXPERIMENT":
              return {
                type: "MLFLOW_EXPERIMENT",
                mlflow_experiment: {
                  experiment_id: trace.trace_location.experimentId,
                },
              };
            case "INFERENCE_TABLE":
              return {
                type: "INFERENCE_TABLE",
                inference_table: {
                  full_table_name: trace.trace_location.fullTableName,
                },
              };
            default:
              return {
                type: "MLFLOW_EXPERIMENT",
                mlflow_experiment: { experiment_id: "" },
              };
          }
        })(),
        request_preview: trace.trace_data.request,
        response_preview: trace.trace_data.response,
        request_time: trace.trace_info.timestamp_ms
          ? new Date(trace.trace_info.timestamp_ms).toISOString()
          : new Date().toISOString(),
        execution_duration: trace.trace_info.execution_duration || "0s",
        state: trace.trace_info.state || "OK",
        trace_metadata: {
          ...trace.trace_info.request_metadata,
          ...(sourceRunUuid && { "mlflow.sourceRun": sourceRunUuid }),
        },
        tags: trace.trace_info.tags || {},
      },
    },
  };

  const response = await workspaceFetch(`/ajax-api/3.0/mlflow/traces`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  const createdTrace = await response.json();

  // Return in the expected format - the response should contain the trace with trace_info
  return {
    trace_id:
      createdTrace.trace?.trace_info?.trace_id ||
      `tr-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    trace_location: trace.trace_location,
    trace_info: {
      trace_id: createdTrace.trace?.trace_info?.trace_id,
      timestamp_ms: trace.trace_info.timestamp_ms || Date.now(),
      execution_duration: trace.trace_info.execution_duration,
      state: trace.trace_info.state,
      request_metadata: request.trace.trace_info.trace_metadata,
      tags: trace.trace_info.tags,
    },
    trace_data: trace.trace_data,
  };
};

const batchCreateLabelingSessionItems = async ({
  reviewAppId,
  labelingSessionId,
  experimentId,
  sourceRunUuid,
  traces,
  getTrace,
}: {
  reviewAppId: string;
  labelingSessionId: string;
  experimentId: string;
  sourceRunUuid?: string;
  traces: RunEvaluationTracesDataEntry[];
  getTrace: (
    requestId?: string,
    traceId?: string
  ) => Promise<ModelTrace | undefined>;
}): Promise<BatchCreateDatasetRecordsResponse> => {
  // Check safex flag to determine copy vs link behavior
  // safe=false (default): copy traces (current behavior for now)
  // safe=true: link traces (safer, non-destructive approach)
  const useTraceInputLinking = safex(
    "databricks.fe.mlflow.useRunIdFilterInSearchTraces",
    false
  );

  let labelingSessionItems: LabelingSessionItem[];

  if (useTraceInputLinking) {
    // Safe mode: use existing trace IDs without copying
    labelingSessionItems = traces.map((trace) => ({
      source: {
        trace_id: trace.traceInfo?.trace_id || trace.requestId,
      },
    }));

    // Link traces to run if sourceRunUuid is provided
    if (sourceRunUuid) {
      const traceIds = traces
        .map((trace) => trace.traceInfo?.trace_id || trace.requestId)
        .filter((id): id is string => Boolean(id));

      if (traceIds.length > 0) {
        await linkTracesToRun(sourceRunUuid, traceIds);
      }
    }
  } else {
    // Default mode: copy traces to the target experiment
    // First collect all of the traces (traces are just TraceInfos, we need the ModelTrace data).
    const tracePromises = traces.map((trace) =>
      getTrace(trace.requestId, trace.traceInfo?.trace_id)
    );
    const modelTraces = await Promise.all(tracePromises);

    // Map modelTraces to CreateTracePayloads.
    const createTracePayloads: CreateTracePayload[] = modelTraces.map(
      (traceV2, index) => {
        const traceInfoV3 = traces[index].traceInfo;
        if (!traceV2) {
          throw new Error(
            `Failed to fetch trace data for trace ${traces[index].requestId}`
          );
        }
        const traceInfoV2 = traceV2.info as
          | ModelTraceInfo
          | NotebookModelTraceInfo;
        const trace: CreateTracePayload = {
          trace_location: {
            type: "MLFLOW_EXPERIMENT",
            experimentId,
          },
          trace_info: {
            timestamp_ms: traceInfoV2.timestamp_ms || Date.now(),
            execution_duration: traceInfoV3?.execution_duration
              ? traceInfoV3?.execution_duration
              : traceInfoV2?.execution_time_ms
              ? formatDuration(traceInfoV2.execution_time_ms)
              : undefined,
            state:
              traceInfoV2.status === "UNSET"
                ? "STATE_UNSPECIFIED"
                : traceInfoV2.status || traceInfoV3?.state,
            request_metadata: traceInfoV2.request_metadata as Record<
              string,
              string
            >,
            tags: traceInfoV2.tags as Record<string, string>,
          },
          trace_data: {
            request: traceV2.data.spans[0].attributes?.["mlflow.spanInputs"],
            response: traceV2.data.spans[0].attributes?.["mlflow.spanOutputs"],
            spans: traceV2.data.spans,
          },
        };
        return trace;
      }
    );

    // Create all of the traces.
    const createdTraces = await Promise.all(
      createTracePayloads.map((trace) => createTrace(trace, sourceRunUuid))
    );

    // Create the LabelingSessionItems using the new trace IDs.
    labelingSessionItems = createdTraces.map((createdTrace) => ({
      source: {
        trace_id: createdTrace.trace_info.trace_id,
      },
    }));
  }

  const batchCreateLabelingSessionItemsRequest: BatchCreateLabelingSessionItemsRequest =
    {
      review_app_id: reviewAppId,
      labeling_session_id: labelingSessionId,
      items: labelingSessionItems,
    };

  return workspaceFetch(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions/${labelingSessionId}/items:batchCreate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(batchCreateLabelingSessionItemsRequest),
    }
  ).then((response) => {
    return response.json();
  });
};

export const useBatchCreateLabelingSessionItems = () =>
  useMutation({
    mutationFn: batchCreateLabelingSessionItems,
  });

async function createDataset(
  name: string,
  experimentIds: string[] = []
): Promise<Dataset> {
  const url = new URL(
    "/ajax-api/2.0/managed-evals/datasets",
    window.location.origin
  );

  // Add experiment_ids as query parameters if provided
  if (experimentIds.length > 0) {
    url.searchParams.set("experiment_ids", experimentIds.join(","));
  }

  const requestBody = {
    name,
    // Other optional fields can be added here if needed:
    // digest, source, source_type
  };

  const response = await workspaceFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  const responseData = await response.json();

  // Also check for error_code in response body even with 200 status (defensive)
  if (responseData.error_code) {
    const errorMessage =
      responseData.message || `Error: ${responseData.error_code}`;
    throw new Error(errorMessage);
  }

  const dataset: Dataset = responseData;
  return dataset;
}

export function useCreateDatasetMutation(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      name,
      experimentIds,
    }: {
      name: string;
      experimentIds?: string[];
    }) => {
      // If no experiment IDs provided, use the current experiment
      const finalExperimentIds = experimentIds || [experimentId];
      return createDataset(name, finalExperimentIds);
    },
    onSuccess: (newDataset) => {
      // Simply add the new dataset to the beginning of the list
      queryClient.setQueryData(
        ["listDatasets", experimentId],
        (oldData: Dataset[] | undefined) => {
          const currentData = oldData || [];
          // Add the new dataset at the beginning
          return [newDataset, ...currentData];
        }
      );
    },
    onError: (err) => {
      // Error handling - no need to rollback since we didn't do optimistic updates
    },
  });
}
