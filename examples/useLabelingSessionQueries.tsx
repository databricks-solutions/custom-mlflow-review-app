import React, { useCallback } from "react";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@databricks/web-shared/query-client";
import { workspaceFetch } from "@databricks/web-shared/spog/workspace-console";
import { isNil } from "lodash";
import { safex } from "@databricks/web-shared/flags";
import { MlflowService } from "../../../sdk/MlflowService";
import { RunEntity } from "../../../types";
import type {
  ModelTrace,
  ModelTraceInfoV3,
  ModelTraceInfo,
  ModelTraceLocation,
  ModelTraceData,
  ModelTraceSpan,
} from "@databricks/web-shared/model-trace-explorer";
import {
  useAddUsersToExperiment,
  useExperimentDetails,
} from "./useExperimentPermissions";
import DatabricksUtils from "../../../../common/utils/DatabricksUtils";

// Types based on the proto definition
interface ReviewApp {
  review_app_id?: string;
  experiment_id?: string;
  agents?: Agent[];
  labeling_schemas?: LabelingSchema[];
}

interface Agent {
  agent_name?: string;
  model_serving_endpoint?: {
    endpoint_name?: string;
    served_entity_name?: string;
  };
}

interface LabelingSchema {
  name?: string;
  type?: "FEEDBACK" | "EXPECTATION";
  title?: string;
  instruction?: string;
  enable_comment?: boolean;
  categorical?: {
    options?: string[];
  };
  categorical_list?: {
    options?: string[];
  };
  text?: {
    max_length?: number;
  };
  text_list?: {
    max_length_each?: number;
    max_count?: number;
  };
  numeric?: {
    min_value?: number;
    max_value?: number;
  };
}

interface ListReviewAppsResponse {
  review_apps?: ReviewApp[];
  next_page_token?: string;
}

interface LabelingSession {
  labeling_session_id?: string;
  mlflow_run_id?: string;
  create_time?: string;
  created_by?: string;
  last_update_time?: string;
  last_updated_by?: string;
  name?: string;
  assigned_users?: string[];
  agent?: {
    agent_name?: string;
  };
  labeling_schemas?: Array<{
    name?: string;
  }>;
  dataset?: {
    dataset_id?: string;
    enable_auto_sync?: boolean;
  };
  additional_configs?: {
    allow_edit_inputs?: boolean;
    disable_multi_turn_chat?: boolean;
    custom_inputs_json?: string;
  };
}

// Hydrated labeling session that includes run metadata
interface HydratedLabelingSession extends LabelingSession {
  run?: RunEntity;
}

interface ListLabelingSessionsResponse {
  labeling_sessions?: LabelingSession[];
  next_page_token?: string;
}

// Item interface from the proto
interface Item {
  item_id?: string;
  create_time?: string;
  created_by?: string;
  last_update_time?: string;
  last_updated_by?: string;
  source?: {
    dataset_record?: {
      dataset_id?: string;
      dataset_record_id?: string;
    };
    trace_id?: string;
  };
  state?: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED";
  chat_rounds?: Array<{
    trace_id?: string;
    dataset_record?: {
      dataset_id?: string;
      dataset_record_id?: string;
    };
  }>;
}

// Hydrated item with trace information
interface HydratedItem extends Item {
  source_trace_info?: ModelTraceInfoV3;
  chat_rounds?: Array<{
    trace_id?: string;
    trace_info?: ModelTraceInfoV3;
    dataset_record?: {
      dataset_id?: string;
      dataset_record_id?: string;
    };
  }>;
}

interface ListItemsResponse {
  items?: Item[];
  next_page_token?: string;
}

// Types for dataset records
interface DatasetRecord {
  dataset_record_id?: string;
  source?: {
    trace?: {
      trace_id?: string;
    };
  };
}

// Types for trace creation payload - use actual ModelTrace types
interface CreateTracePayload {
  trace_location: ModelTraceLocation;
  trace_info: ModelTraceInfoV3;
  trace_data: ModelTraceData;
}

// API result interface for createTrace function
interface CreateTraceResult {
  trace_id: string;
  trace_location: ModelTraceLocation;
  trace_info: ModelTraceInfoV3;
  trace_data: ModelTraceData;
}

// API Functions
const listReviewApps = async (filter?: string): Promise<ReviewApp[]> => {
  let nextPageToken = undefined;
  let shouldFetch = true;
  let reviewApps: ReviewApp[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    const url = new URL(
      "/ajax-api/2.0/managed-evals/review-apps",
      window.location.origin
    );

    // Set the query params
    url.searchParams.set("page_size", "500");

    if (filter) {
      url.searchParams.set("filter", filter);
    }

    if (nextPageToken) {
      url.searchParams.set("page_token", nextPageToken);
    }

    const res = await workspaceFetch(url);

    if (!res.ok) {
      try {
        const errorBody = await res.json();
        const errorMessage =
          errorBody?.message ||
          `Failed to fetch review apps: ${res.status} ${res.statusText}`;
        throw new Error(errorMessage);
      } catch (parseError) {
        // If parsing fails, fall back to status text
        throw new Error(
          `Failed to fetch review apps: ${res.status} ${res.statusText}`
        );
      }
    }

    const response: ListReviewAppsResponse = await res.json();
    nextPageToken = response.next_page_token;

    if (response.review_apps) {
      reviewApps = reviewApps.concat(response.review_apps);
    }

    shouldFetch = false;
  }

  return reviewApps;
};

const updateReviewApp = async (
  reviewAppId: string,
  reviewApp: ReviewApp,
  updateMask: string
): Promise<ReviewApp> => {
  const url = new URL(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}`,
    window.location.origin
  );

  // Add update_mask as a query parameter
  url.searchParams.set("update_mask", updateMask);

  const response = await workspaceFetch(url, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(reviewApp),
  });

  if (!response.ok) {
    // Try to parse the error response body to get the actual error message
    try {
      const errorBody = await response.json();
      const errorMessage =
        errorBody?.message ||
        `Failed to update review app: ${response.statusText}`;
      throw new Error(errorMessage);
    } catch (parseError) {
      // If parsing fails, fall back to status text
      throw new Error(`Failed to update review app: ${response.statusText}`);
    }
  }

  return response.json();
};

const createReviewApp = async (experimentId: string): Promise<ReviewApp> => {
  const url = new URL(
    "/ajax-api/2.0/managed-evals/review-apps",
    window.location.origin
  );

  const reviewApp: ReviewApp = {
    experiment_id: experimentId,
    agents: [],
    labeling_schemas: [],
  };

  const response = await workspaceFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(reviewApp),
  });

  if (!response.ok) {
    // Try to parse the error response body to get the actual error message
    try {
      const errorBody = await response.json();
      const errorMessage =
        errorBody?.message ||
        `Failed to create review app: ${response.statusText}`;
      throw new Error(errorMessage);
    } catch (parseError) {
      // If parsing fails, fall back to status text
      throw new Error(`Failed to create review app: ${response.statusText}`);
    }
  }

  return response.json();
};

const listLabelingSessions = async (
  reviewAppId: string
): Promise<LabelingSession[]> => {
  let nextPageToken = undefined;
  let shouldFetch = true;
  let labelingSessions: LabelingSession[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    const url = new URL(
      `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions`,
      window.location.origin
    );

    // Set the query params
    url.searchParams.set("page_size", "500");

    if (nextPageToken) {
      url.searchParams.set("page_token", nextPageToken);
    }

    const response: ListLabelingSessionsResponse = await workspaceFetch(
      url
    ).then((res: Response) => res.json());
    nextPageToken = response.next_page_token;

    if (response.labeling_sessions) {
      labelingSessions = labelingSessions.concat(response.labeling_sessions);
    }

    shouldFetch = false;
  }

  return labelingSessions;
};

const listLabelingSessionItems = async (
  reviewAppId: string,
  labelingSessionId: string
): Promise<Item[]> => {
  let nextPageToken = undefined;
  let shouldFetch = true;
  let items: Item[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    const url = new URL(
      `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions/${labelingSessionId}/items`,
      window.location.origin
    );

    // Set the query params
    url.searchParams.set("page_size", "500");

    if (nextPageToken) {
      url.searchParams.set("page_token", nextPageToken);
    }

    const response: ListItemsResponse = await workspaceFetch(url).then(
      (res: Response) => res.json()
    );
    nextPageToken = response.next_page_token;

    if (response.items) {
      items = items.concat(response.items);
    }

    shouldFetch = false;
  }

  return items;
};

const createLabelingSession = async (
  reviewAppId: string,
  labelingSession: LabelingSession
): Promise<LabelingSession> => {
  const url = new URL(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions`,
    window.location.origin
  );

  const response = await workspaceFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(labelingSession),
  });

  if (!response.ok) {
    // Try to parse the error response body to get the actual error message
    const errorBody = await response.json();
    const errorMessage =
      errorBody?.message ||
      `Failed to create labeling session: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

const updateLabelingSession = async (
  reviewAppId: string,
  labelingSessionId: string,
  labelingSession: LabelingSession,
  updateMask: string
): Promise<LabelingSession> => {
  const url = new URL(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions/${labelingSessionId}`,
    window.location.origin
  );

  // Add update_mask as a query parameter
  url.searchParams.set("update_mask", updateMask);

  const response = await workspaceFetch(url, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(labelingSession),
  });

  if (!response.ok) {
    // Try to parse the error response body to get the actual error message
    try {
      const errorBody = await response.json();
      const errorMessage =
        errorBody?.message ||
        `Failed to update labeling session: ${response.statusText}`;
      throw new Error(errorMessage);
    } catch (parseError) {
      // If parsing fails, fall back to status text
      throw new Error(
        `Failed to update labeling session: ${response.statusText}`
      );
    }
  }

  return response.json();
};

const deleteLabelingSession = async (
  reviewAppId: string,
  labelingSessionId: string
): Promise<void> => {
  const url = new URL(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions/${labelingSessionId}`,
    window.location.origin
  );

  const response = await workspaceFetch(url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    // Try to parse the error response body to get the actual error message
    try {
      const errorBody = await response.json();
      const errorMessage =
        errorBody?.message ||
        `Failed to delete labeling session: ${response.statusText}`;
      throw new Error(errorMessage);
    } catch (parseError) {
      // If parsing fails, fall back to status text
      throw new Error(
        `Failed to delete labeling session: ${response.statusText}`
      );
    }
  }
};

// Placeholder for MLflow run creation - will be implemented later
const createMLflowRun = async (
  experimentId: string,
  runName?: string
): Promise<{ runUuid: string }> => {
  // TODO: Implement MLflow run creation
  // For now, return a placeholder
  return Promise.resolve({ runUuid: "placeholder-run-uuid" });
};

// Function to fetch experiment runs (similar to useExperimentEvaluationRunsData)
const fetchExperimentRuns = async (
  experimentId: string
): Promise<RunEntity[]> => {
  const requestBody = {
    experiment_ids: [experimentId],
    order_by: ["attributes.start_time DESC"],
    filter: "", // No filter, we want all runs
  };

  const response = await MlflowService.searchRuns(requestBody);
  return response.runs || [];
};

// Function to fetch trace info for multiple trace IDs using V3 API
const fetchTraceInfos = async (
  traceIds: string[]
): Promise<Map<string, ModelTraceInfoV3>> => {
  const traceInfoMap = new Map<string, ModelTraceInfoV3>();

  // Fetch trace infos in parallel
  const promises = traceIds.map(async (traceId) => {
    try {
      const response = await MlflowService.getExperimentTraceInfoV3(traceId);
      if (response.trace?.trace_info) {
        // Convert ModelTraceInfo to ModelTraceInfoV3 format if needed
        const traceInfo = response.trace.trace_info as any;

        // If it's already v3 format, use it directly
        if (traceInfo.trace_id && traceInfo.trace_location) {
          traceInfoMap.set(traceId, traceInfo as ModelTraceInfoV3);
        } else {
          // Convert from v2 to v3 format
          const v3TraceInfo: ModelTraceInfoV3 = {
            trace_id: traceId,
            trace_location: {
              type: "MLFLOW_EXPERIMENT",
              mlflow_experiment: {
                experiment_id: traceInfo.experiment_id || "",
              },
            },
            request_time: traceInfo.timestamp_ms
              ? new Date(traceInfo.timestamp_ms).toISOString()
              : new Date().toISOString(),
            execution_duration: traceInfo.execution_time_ms
              ? `${traceInfo.execution_time_ms / 1000}s`
              : "0s",
            state:
              traceInfo.status === "UNSET"
                ? "STATE_UNSPECIFIED"
                : traceInfo.status || "OK",
            trace_metadata: Object.fromEntries(
              (traceInfo.request_metadata || []).map((item: any) => [
                item.key,
                item.value,
              ])
            ),
            tags: Object.fromEntries(
              (traceInfo.tags || []).map((item: any) => [item.key, item.value])
            ),
            assessments: [],
          };
          traceInfoMap.set(traceId, v3TraceInfo);
        }
      }
    } catch (error) {
      // Silently ignore trace fetch errors as they are expected when some traces are unavailable
      // The trace info will simply be undefined for those traces
    }
  });

  await Promise.all(promises);
  return traceInfoMap;
};

// Function to hydrate items with trace information
const hydrateItemsWithTraceInfo = async (
  items: Item[]
): Promise<HydratedItem[]> => {
  // Collect all unique trace IDs
  const traceIds = new Set<string>();

  items.forEach((item) => {
    // Add source trace ID if it exists
    if (item.source?.trace_id) {
      traceIds.add(item.source.trace_id);
    }

    // Add chat round trace IDs if they exist
    item.chat_rounds?.forEach((round) => {
      if (round.trace_id) {
        traceIds.add(round.trace_id);
      }
    });
  });

  // Fetch all trace infos
  const traceInfoMap = await fetchTraceInfos(Array.from(traceIds));

  // Hydrate items with trace information
  return items.map((item): HydratedItem => {
    const hydratedItem: HydratedItem = { ...item };

    // Add source trace info
    if (item.source?.trace_id) {
      hydratedItem.source_trace_info = traceInfoMap.get(item.source.trace_id);
    }

    // Add chat rounds trace info
    if (item.chat_rounds) {
      hydratedItem.chat_rounds = item.chat_rounds.map((round) => ({
        trace_id: round.trace_id,
        trace_info: round.trace_id
          ? traceInfoMap.get(round.trace_id)
          : undefined,
        dataset_record: round.dataset_record,
      }));
    }

    return hydratedItem;
  });
};

// Custom hook to get or create review app for an experiment
export const useGetReviewApp = (experimentId: string) => {
  const queryClient = useQueryClient();

  // Query to list review apps filtered by experiment ID
  const {
    data: reviewApps,
    isLoading: isListLoading,
    error: listError,
  } = useQuery({
    queryKey: ["reviewApps", "list", experimentId],
    queryFn: () => listReviewApps(`experiment_id=${experimentId}`),
    enabled: !!experimentId,
    staleTime: Infinity, // Never consider data stale
    cacheTime: Infinity, // Cache forever
    refetchOnWindowFocus: false, // Don't refetch on window focus
    refetchOnMount: false, // Don't refetch when component mounts if data exists
    refetchOnReconnect: false, // Don't refetch on network reconnect
    retry: false, // Don't retry failed requests
  });

  // Mutation to create review app if none exists - use shared mutation key to prevent parallel creations
  const createMutation = useMutation({
    mutationFn: (experimentId: string) => createReviewApp(experimentId),
    retry: false, // Don't retry failed requests
    onSuccess: (newReviewApp) => {
      // Update the cache with the new review app
      queryClient.setQueryData(
        ["reviewApps", "list", experimentId],
        [newReviewApp]
      );
    },
  });

  // Check if there's already a pending creation mutation for this experiment
  const pendingCreations = queryClient.getMutationCache().findAll({
    mutationKey: ["createReviewApp", experimentId],
    predicate: (mutation) => mutation.state.status === "loading",
  });

  const isCreationInProgress = pendingCreations.length > 0;

  // Automatically create a review app if none exists and the list query has completed
  React.useEffect(() => {
    if (
      !isListLoading &&
      !listError &&
      reviewApps &&
      reviewApps.length === 0 &&
      !createMutation.isLoading &&
      !isCreationInProgress
    ) {
      // No review app exists and no creation is in progress, create one automatically
      createMutation.mutate(experimentId);
    }
  }, [
    reviewApps,
    isListLoading,
    listError,
    experimentId,
    createMutation,
    isCreationInProgress,
  ]);

  // Get existing review app or create new one
  const getReviewApp = useCallback(async (): Promise<ReviewApp> => {
    // If we already have a review app, return it
    const existingApps = reviewApps || [];
    if (existingApps.length > 0) {
      return existingApps[0];
    }

    // Check if creation is already in progress
    const currentPendingCreations = queryClient.getMutationCache().findAll({
      mutationKey: ["createReviewApp", experimentId],
      predicate: (mutation) => mutation.state.status === "loading",
    });

    if (currentPendingCreations.length > 0) {
      // Wait for the existing creation to complete
      const pendingMutation = currentPendingCreations[0];
      try {
        const result = await (pendingMutation as any).promise;
        return result as ReviewApp;
      } catch (error) {
        // If the pending mutation failed, try to create again
        const createdApp = await createMutation.mutateAsync(experimentId);
        return createdApp;
      }
    }

    // If no review app exists and no creation is in progress, create one
    const createdApp = await createMutation.mutateAsync(experimentId);
    return createdApp;
  }, [reviewApps, experimentId, createMutation, queryClient]);

  // Determine the current review app
  const reviewApp = reviewApps?.[0] || null;
  const isLoadingReviewApp =
    isListLoading || createMutation.isLoading || isCreationInProgress;
  const error = listError || createMutation.error;

  return {
    reviewApp,
    getReviewApp,
    isLoading: isLoadingReviewApp,
    error,
    refetch: () =>
      queryClient.invalidateQueries({
        queryKey: ["reviewApps", "list", experimentId],
      }),
  };
};

// New hook to get hydrated labeling sessions with run metadata
export const useHydratedLabelingSessions = (experimentId?: string) => {
  // Get review app
  const {
    reviewApp,
    isLoading: isReviewAppLoading,
    error: reviewAppError,
  } = useGetReviewApp(experimentId || "");

  // Query labeling sessions
  const labelingSessionsQuery = useQuery({
    queryKey: ["labelingSessions", "list", reviewApp?.review_app_id],
    queryFn: () => {
      if (!reviewApp?.review_app_id) {
        throw new Error("Review app ID is required");
      }
      return listLabelingSessions(reviewApp.review_app_id);
    },
    enabled:
      !!experimentId && !!reviewApp?.review_app_id && !isReviewAppLoading,
    refetchOnWindowFocus: false,
  });

  // Query experiment runs in parallel
  const runsQuery = useQuery({
    queryKey: ["experimentRuns", experimentId],
    queryFn: () => fetchExperimentRuns(experimentId || ""),
    enabled: !!experimentId,
    refetchOnWindowFocus: false,
  });

  // Combine the data
  const hydratedSessions: HydratedLabelingSession[] = React.useMemo(() => {
    if (!labelingSessionsQuery.data || !runsQuery.data) {
      return [];
    }

    // Create a map of run UUID to run for quick lookup
    const runMap = new Map<string, RunEntity>();
    runsQuery.data.forEach((run) => {
      runMap.set(run.info.runUuid, run);
    });

    // Hydrate labeling sessions with run data
    return labelingSessionsQuery.data.map((session) => ({
      ...session,
      run: session.mlflow_run_id
        ? runMap.get(session.mlflow_run_id)
        : undefined,
    }));
  }, [labelingSessionsQuery.data, runsQuery.data]);

  return {
    data: hydratedSessions,
    isLoading:
      isReviewAppLoading ||
      labelingSessionsQuery.isLoading ||
      runsQuery.isLoading,
    isFetching: labelingSessionsQuery.isFetching || runsQuery.isFetching,
    error: reviewAppError || labelingSessionsQuery.error || runsQuery.error,
    refetch: () => {
      labelingSessionsQuery.refetch();
      runsQuery.refetch();
    },
  };
};

// Hook to get hydrated items for a labeling session (items + trace info)
export const useHydratedLabelingSessionItems = (
  experimentId?: string,
  labelingSessionId?: string
) => {
  // Get review app for this experiment
  const {
    reviewApp,
    isLoading: isReviewAppLoading,
    error: reviewAppError,
  } = useGetReviewApp(experimentId || "");

  return useQuery({
    queryKey: [
      "labelingSessionItems",
      "hydrated",
      reviewApp?.review_app_id,
      labelingSessionId,
    ],
    queryFn: async () => {
      if (!reviewApp?.review_app_id) {
        throw new Error("Review app ID is required");
      }
      if (!labelingSessionId) {
        throw new Error("Labeling session ID is required");
      }

      // First fetch the items
      const items = await listLabelingSessionItems(
        reviewApp.review_app_id,
        labelingSessionId
      );

      // Then hydrate them with trace information
      return hydrateItemsWithTraceInfo(items);
    },
    enabled:
      !!experimentId &&
      !!labelingSessionId &&
      !!reviewApp?.review_app_id &&
      !isReviewAppLoading,
    // Include review app loading state and errors in metadata
    meta: {
      isReviewAppLoading,
      reviewAppError,
    },
  });
};

// Hook to create a new labeling session
export const useCreateLabelingSession = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);
  const addUsersToExperimentMutation = useAddUsersToExperiment();
  const { data: experiment } = useExperimentDetails(experimentId);

  return useMutation({
    mutationFn: async (labelingSessionData: {
      name: string;
      assigned_users?: string[];
      agent?: string;
      labeling_schemas?: string[];
      custom_inputs?: Record<string, any>;
      dataset_id?: string;
    }) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error(
          "Review app ID is required to create a labeling session"
        );
      }

      // Validate that all specified label schemas exist in the review app
      const validSchemaNames = new Set(
        (currentReviewApp.labeling_schemas || []).map((schema) => schema.name)
      );

      if (labelingSessionData.labeling_schemas) {
        for (const schemaName of labelingSessionData.labeling_schemas) {
          if (!validSchemaNames.has(schemaName)) {
            throw new Error(
              `Label schema '${schemaName}' not found. Please create it first via 'create_label_schema'.`
            );
          }
        }
      }

      // Validate that the agent exists in the review app if specified
      if (labelingSessionData.agent) {
        const agentExists = (currentReviewApp.agents || []).some(
          (agent) => agent.agent_name === labelingSessionData.agent
        );

        if (!agentExists) {
          throw new Error(
            `Agent '${labelingSessionData.agent}' not found in the review app. ` +
              "Please add the agent first using the add_agent method."
          );
        }
      }

      // First create an MLflow run (placeholder for now)
      const mlflowRun = await createMLflowRun(
        experimentId,
        labelingSessionData.name
      );

      // Create the labeling session with the validated data
      const labelingSessionToCreate: LabelingSession = {
        name: labelingSessionData.name,
        assigned_users: labelingSessionData.assigned_users || [],
        agent: labelingSessionData.agent
          ? { agent_name: labelingSessionData.agent }
          : undefined,
        labeling_schemas: (labelingSessionData.labeling_schemas || []).map(
          (name) => ({ name })
        ),
        dataset: labelingSessionData.dataset_id
          ? {
              dataset_id: labelingSessionData.dataset_id,
              enable_auto_sync: true,
            }
          : undefined,
        additional_configs: {
          disable_multi_turn_chat: true,
          custom_inputs_json: labelingSessionData.custom_inputs
            ? JSON.stringify(labelingSessionData.custom_inputs)
            : undefined,
        },
        // The service will create the run.
        mlflow_run_id: undefined,
      };

      // Validate that name is not empty
      if (
        !labelingSessionToCreate.name ||
        labelingSessionToCreate.name.trim() === ""
      ) {
        throw new Error("Session name is required and cannot be empty");
      }

      const createdSession = await createLabelingSession(
        currentReviewApp.review_app_id,
        labelingSessionToCreate
      );

      // Return both the session and the assigned users for use in onSuccess
      return {
        session: createdSession,
        assignedUsers: labelingSessionData.assigned_users || [],
      };
    },
    onSuccess: async (result) => {
      const { session: newLabelingSession, assignedUsers } = result;

      // Invalidate and refetch labeling sessions list
      queryClient.invalidateQueries({
        queryKey: ["labelingSessions", "list", reviewApp?.review_app_id],
      });

      // Also invalidate the hydrated sessions
      queryClient.invalidateQueries({
        queryKey: ["experimentRuns", experimentId],
      });

      // Grant experiment permissions to assigned users
      if (assignedUsers.length > 0) {
        try {
          const currentUserEmail = DatabricksUtils.getConf("user")?.toString();

          // Filter out current user and prepare users array for batch permission grant
          const usersToGrant = assignedUsers
            .map((userEmail) => userEmail.trim())
            .filter((userEmail) => userEmail && userEmail !== currentUserEmail)
            .map((userEmail) => ({
              userName: userEmail,
              permissionLevel: "CAN_EDIT" as const,
            }));

          if (usersToGrant.length > 0) {
            try {
              await addUsersToExperimentMutation.mutateAsync({
                experimentId,
                users: usersToGrant,
              });
            } catch (permissionError) {
              // Silently handle permission errors to not block labeling session creation
              // In production, these could be logged to a monitoring service
            }
          }
        } catch (error) {
          // Silently handle general permission errors
          // In production, these could be logged to a monitoring service
        }
      }
    },
  });
};

// Hook to update an existing labeling session
export const useUpdateLabelingSession = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);
  const addUsersToExperimentMutation = useAddUsersToExperiment();
  const { data: experiment } = useExperimentDetails(experimentId);

  return useMutation({
    mutationFn: async (params: {
      labelingSessionId: string;
      updates: {
        name?: string;
        assigned_users?: string[];
        labeling_schemas?: string[];
        custom_inputs?: Record<string, any>;
      };
    }) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error(
          "Review app ID is required to update a labeling session"
        );
      }

      // Validate that all specified label schemas exist in the review app
      if (params.updates.labeling_schemas) {
        const validSchemaNames = new Set(
          (currentReviewApp.labeling_schemas || []).map((schema) => schema.name)
        );

        for (const schemaName of params.updates.labeling_schemas) {
          if (!validSchemaNames.has(schemaName)) {
            throw new Error(
              `Label schema '${schemaName}' not found. Please create it first via 'create_label_schema'.`
            );
          }
        }
      }

      // Build the labeling session update payload
      const labelingSessionToUpdate: Partial<LabelingSession> = {};
      const updateFields: string[] = [];

      if (params.updates.name !== undefined) {
        labelingSessionToUpdate.name = params.updates.name;
        updateFields.push("name");
      }

      if (params.updates.assigned_users !== undefined) {
        labelingSessionToUpdate.assigned_users = params.updates.assigned_users;
        updateFields.push("assigned_users");
      }

      if (params.updates.labeling_schemas !== undefined) {
        labelingSessionToUpdate.labeling_schemas =
          params.updates.labeling_schemas.map((name) => ({ name }));
        updateFields.push("labeling_schemas");
      }

      if (params.updates.custom_inputs !== undefined) {
        labelingSessionToUpdate.additional_configs = {
          disable_multi_turn_chat: true,
          custom_inputs_json: params.updates.custom_inputs
            ? JSON.stringify(params.updates.custom_inputs)
            : undefined,
        };
        updateFields.push("additional_configs");
      }

      // Validate that name is not empty if provided
      if (
        labelingSessionToUpdate.name !== undefined &&
        (!labelingSessionToUpdate.name ||
          labelingSessionToUpdate.name.trim() === "")
      ) {
        throw new Error("Session name is required and cannot be empty");
      }

      const updateMask = updateFields.join(",");

      const updatedLabelingSession = await updateLabelingSession(
        currentReviewApp.review_app_id,
        params.labelingSessionId,
        labelingSessionToUpdate,
        updateMask
      );

      // Return both the updated session and the assigned users for use in onSuccess
      return {
        session: updatedLabelingSession,
        assignedUsers: params.updates.assigned_users || [],
      };
    },
    onSuccess: async (result) => {
      const { assignedUsers } = result;

      // Invalidate and refetch labeling sessions list
      queryClient.invalidateQueries({
        queryKey: ["labelingSessions", "list", reviewApp?.review_app_id],
      });

      // Also invalidate the hydrated sessions
      queryClient.invalidateQueries({
        queryKey: ["experimentRuns", experimentId],
      });

      // Grant experiment permissions to assigned users (only if assigned_users was updated)
      if (assignedUsers.length > 0) {
        try {
          const currentUserEmail = DatabricksUtils.getConf("user")?.toString();

          // Filter out current user and prepare users array for batch permission grant
          const usersToGrant = assignedUsers
            .map((userEmail) => userEmail.trim())
            .filter((userEmail) => userEmail && userEmail !== currentUserEmail)
            .map((userEmail) => ({
              userName: userEmail,
              permissionLevel: "CAN_EDIT" as const,
            }));

          if (usersToGrant.length > 0) {
            try {
              await addUsersToExperimentMutation.mutateAsync({
                experimentId,
                users: usersToGrant,
              });
            } catch (permissionError) {
              // Silently handle permission errors to not block labeling session update
              // In production, these could be logged to a monitoring service
            }
          }
        } catch (error) {
          // Silently handle general permission errors
          // In production, these could be logged to a monitoring service
        }
      }
    },
  });
};

// Hook to delete a labeling session
export const useDeleteLabelingSession = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);

  return useMutation({
    mutationFn: async (labelingSessionId: string) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error(
          "Review app ID is required to delete a labeling session"
        );
      }

      return deleteLabelingSession(
        currentReviewApp.review_app_id,
        labelingSessionId
      );
    },
    onSuccess: () => {
      // Invalidate and refetch labeling sessions list
      queryClient.invalidateQueries({
        queryKey: ["labelingSessions", "list", reviewApp?.review_app_id],
      });

      // Also invalidate the hydrated sessions
      queryClient.invalidateQueries({
        queryKey: ["experimentRuns", experimentId],
      });
    },
  });
};

// Hook to create a new label schema
export const useCreateLabelSchema = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);

  return useMutation({
    mutationFn: async (labelSchemaData: {
      name: string;
      type: "FEEDBACK" | "EXPECTATION";
      title: string;
      instruction?: string;
      enable_comment?: boolean;
      categorical?: {
        options: string[];
      };
      categorical_list?: {
        options: string[];
      };
      text?: {
        max_length?: number;
      };
      text_list?: {
        max_length_each?: number;
        max_count?: number;
      };
      numeric?: {
        min_value?: number;
        max_value?: number;
      };
    }) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error("Review app ID is required to create a label schema");
      }

      // Check if schema with same name already exists
      const existingSchema = (currentReviewApp.labeling_schemas || []).find(
        (schema) => schema.name === labelSchemaData.name
      );
      if (existingSchema) {
        throw new Error(
          `Label schema with name '${labelSchemaData.name}' already exists`
        );
      }

      // Validate that exactly one input type is provided
      const inputTypes = [
        labelSchemaData.categorical,
        labelSchemaData.categorical_list,
        labelSchemaData.text,
        labelSchemaData.text_list,
        labelSchemaData.numeric,
      ].filter(Boolean);

      if (inputTypes.length === 0) {
        throw new Error("At least one input type must be specified");
      }
      if (inputTypes.length > 1) {
        throw new Error("Only one input type can be specified");
      }

      // Create the new schema
      const newSchema: LabelingSchema = {
        name: labelSchemaData.name,
        type: labelSchemaData.type,
        title: labelSchemaData.title,
        instruction: labelSchemaData.instruction,
        enable_comment: labelSchemaData.enable_comment || false,
        categorical: labelSchemaData.categorical,
        categorical_list: labelSchemaData.categorical_list,
        text: labelSchemaData.text,
        text_list: labelSchemaData.text_list,
        numeric: labelSchemaData.numeric,
      };

      // Add the new schema to the existing schemas
      const updatedReviewApp: ReviewApp = {
        ...currentReviewApp,
        labeling_schemas: [
          newSchema,
          ...(currentReviewApp.labeling_schemas || []),
        ],
      };

      // Update the review app with the new schema
      return updateReviewApp(
        currentReviewApp.review_app_id,
        updatedReviewApp,
        "labeling_schemas"
      );
    },
    onMutate: async (labelSchemaData) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });

      // Snapshot the previous value
      const previousReviewApps = queryClient.getQueryData([
        "reviewApps",
        "list",
        experimentId,
      ]) as ReviewApp[];

      // Create the optimistic new schema
      const optimisticSchema: LabelingSchema = {
        name: labelSchemaData.name,
        type: labelSchemaData.type,
        title: labelSchemaData.title,
        instruction: labelSchemaData.instruction,
        enable_comment: labelSchemaData.enable_comment || false,
        categorical: labelSchemaData.categorical,
        categorical_list: labelSchemaData.categorical_list,
        text: labelSchemaData.text,
        text_list: labelSchemaData.text_list,
        numeric: labelSchemaData.numeric,
      };

      // Optimistically update the cache
      queryClient.setQueryData(
        ["reviewApps", "list", experimentId],
        (oldData: ReviewApp[] | undefined) => {
          if (!oldData || oldData.length === 0) return oldData;

          const currentReviewApp = oldData[0];
          const updatedReviewApp: ReviewApp = {
            ...currentReviewApp,
            labeling_schemas: [
              optimisticSchema,
              ...(currentReviewApp.labeling_schemas || []),
            ],
          };

          return [updatedReviewApp];
        }
      );

      // Return context object with the previous value
      return { previousReviewApps };
    },
    onError: (err, labelSchemaData, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousReviewApps) {
        queryClient.setQueryData(
          ["reviewApps", "list", experimentId],
          context.previousReviewApps
        );
      }
    },
    onSettled: () => {
      // Always refetch after error or success to ensure consistency with server
      queryClient.invalidateQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });
    },
  });
};

// Hook to update an existing label schema
export const useUpdateLabelSchema = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);

  return useMutation({
    mutationFn: async (params: {
      originalSchema: LabelingSchema;
      updates: LabelingSchema;
    }) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error("Review app ID is required to update a label schema");
      }

      // Find the schema to update
      const schemaIndex = (currentReviewApp.labeling_schemas || []).findIndex(
        (schema) => schema.name === params.originalSchema.name
      );

      if (schemaIndex === -1) {
        throw new Error(
          `Label schema with name '${params.originalSchema.name}' not found`
        );
      }

      // Check if the name changed and if the new name conflicts
      if (params.updates.name !== params.originalSchema.name) {
        const nameConflict = (currentReviewApp.labeling_schemas || []).some(
          (schema, index) =>
            schema.name === params.updates.name && index !== schemaIndex
        );
        if (nameConflict) {
          throw new Error(
            `Label schema with name '${params.updates.name}' already exists`
          );
        }
      }

      // Update the schema in the list
      const updatedSchemas = [...(currentReviewApp.labeling_schemas || [])];
      updatedSchemas[schemaIndex] = params.updates;

      // Update the review app with the modified schema list
      const updatedReviewApp: ReviewApp = {
        ...currentReviewApp,
        labeling_schemas: updatedSchemas,
      };

      return updateReviewApp(
        currentReviewApp.review_app_id,
        updatedReviewApp,
        "labeling_schemas"
      );
    },
    onMutate: async (params) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });

      // Snapshot the previous value
      const previousReviewApps = queryClient.getQueryData([
        "reviewApps",
        "list",
        experimentId,
      ]) as ReviewApp[];

      // Optimistically update the cache
      queryClient.setQueryData(
        ["reviewApps", "list", experimentId],
        (oldData: ReviewApp[] | undefined) => {
          if (!oldData || oldData.length === 0) return oldData;

          const currentReviewApp = oldData[0];
          const schemaIndex = (
            currentReviewApp.labeling_schemas || []
          ).findIndex((schema) => schema.name === params.originalSchema.name);

          if (schemaIndex === -1) return oldData; // Schema not found, don't update

          // Update the schema in the list
          const updatedSchemas = [...(currentReviewApp.labeling_schemas || [])];
          updatedSchemas[schemaIndex] = params.updates;

          const updatedReviewApp: ReviewApp = {
            ...currentReviewApp,
            labeling_schemas: updatedSchemas,
          };

          return [updatedReviewApp];
        }
      );

      // Return context object with the previous value
      return { previousReviewApps };
    },
    onError: (err, params, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousReviewApps) {
        queryClient.setQueryData(
          ["reviewApps", "list", experimentId],
          context.previousReviewApps
        );
      }
    },
    onSettled: () => {
      // Always refetch after error or success to ensure consistency with server
      queryClient.invalidateQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });
    },
  });
};

// Hook to delete a label schema
export const useDeleteLabelSchema = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp, getReviewApp } = useGetReviewApp(experimentId);

  return useMutation({
    mutationFn: async (schemaToDelete: LabelingSchema) => {
      // Ensure we have a review app
      const currentReviewApp = reviewApp || (await getReviewApp());

      if (!currentReviewApp?.review_app_id) {
        throw new Error("Review app ID is required to delete a label schema");
      }

      // Remove the schema from the list
      const updatedSchemas = (currentReviewApp.labeling_schemas || []).filter(
        (schema) => schema.name !== schemaToDelete.name
      );

      // Update the review app with the modified schema list
      const updatedReviewApp: ReviewApp = {
        ...currentReviewApp,
        labeling_schemas: updatedSchemas,
      };

      return updateReviewApp(
        currentReviewApp.review_app_id,
        updatedReviewApp,
        "labeling_schemas"
      );
    },
    onMutate: async (schemaToDelete) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });

      // Snapshot the previous value
      const previousReviewApps = queryClient.getQueryData([
        "reviewApps",
        "list",
        experimentId,
      ]) as ReviewApp[];

      // Optimistically update the cache
      queryClient.setQueryData(
        ["reviewApps", "list", experimentId],
        (oldData: ReviewApp[] | undefined) => {
          if (!oldData || oldData.length === 0) return oldData;

          const currentReviewApp = oldData[0];

          // Remove the schema from the list
          const updatedSchemas = (
            currentReviewApp.labeling_schemas || []
          ).filter((schema) => schema.name !== schemaToDelete.name);

          const updatedReviewApp: ReviewApp = {
            ...currentReviewApp,
            labeling_schemas: updatedSchemas,
          };

          return [updatedReviewApp];
        }
      );

      // Return context object with the previous value
      return { previousReviewApps };
    },
    onError: (err, schemaToDelete, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousReviewApps) {
        queryClient.setQueryData(
          ["reviewApps", "list", experimentId],
          context.previousReviewApps
        );
      }
    },
    onSettled: () => {
      // Always refetch after error or success to ensure consistency with server
      queryClient.invalidateQueries({
        queryKey: ["reviewApps", "list", experimentId],
      });
    },
  });
};

// Hook to list label schemas for an experiment
export const useListLabelSchemas = (experimentId?: string) => {
  const { reviewApp, isLoading, error, refetch } = useGetReviewApp(
    experimentId || ""
  );

  return {
    data: reviewApp?.labeling_schemas || [],
    isLoading,
    error,
    refetch,
  };
};

// Utility functions that mirror the Python utils.py

// Function to list dataset records (mirrors Python _get_client().list_dataset_records())
const listDatasetRecords = async (
  datasetId: string
): Promise<DatasetRecord[]> => {
  let nextPageToken = undefined;
  let shouldFetch = true;
  let records: DatasetRecord[] = [];

  while (!isNil(nextPageToken) || shouldFetch) {
    const url = new URL(
      `/ajax-api/2.0/managed-evals/datasets/${datasetId}/records`,
      window.location.origin
    );

    url.searchParams.set("page_size", "500");

    if (nextPageToken) {
      url.searchParams.set("page_token", nextPageToken);
    }

    const response = await workspaceFetch(url);
    if (!response.ok) {
      throw new Error(`Failed to list dataset records: ${response.statusText}`);
    }

    const result = await response.json();
    nextPageToken = result.next_page_token;

    if (result.dataset_records) {
      records = records.concat(result.dataset_records);
    }

    shouldFetch = false;
  }

  return records;
};

// Function to batch create items in labeling session (mirrors Python batch_create_items_in_labeling_session)
const batchCreateItemsInLabelingSession = async (
  reviewAppId: string,
  labelingSessionId: string,
  options: {
    traceIds?: string[];
    datasetId?: string;
    datasetRecordIds?: string[];
  }
): Promise<void> => {
  const items: any[] = [];

  // Add trace items
  if (options.traceIds) {
    items.push(
      ...options.traceIds.map((traceId) => ({ source: { trace_id: traceId } }))
    );
  }

  // Add dataset record items
  if (options.datasetId && options.datasetRecordIds) {
    items.push(
      ...options.datasetRecordIds.map((recordId) => ({
        source: {
          dataset_record: {
            dataset_id: options.datasetId,
            dataset_record_id: recordId,
          },
        },
      }))
    );
  }

  if (items.length === 0) {
    return; // Nothing to create
  }

  const url = new URL(
    `/ajax-api/2.0/managed-evals/review-apps/${reviewAppId}/labeling-sessions/${labelingSessionId}/items:batchCreate`,
    window.location.origin
  );

  const response = await workspaceFetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ items }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const errorMessage =
      errorBody?.message ||
      `Failed to batch create items: ${response.statusText}`;
    throw new Error(errorMessage);
  }
};

// Function to log trace to experiment (mirrors Python log_trace_to_experiment)
const logTraceToExperiment = async (
  trace: ModelTrace,
  experimentId: string,
  runId?: string
): Promise<ModelTrace> => {
  // Check safex flag to determine copy vs link behavior
  // safe=false (default): copy traces (current behavior for now)
  // safe=true: link traces (safer, non-destructive approach)
  const useTraceInputLinking = safex(
    "databricks.fe.mlflow.useRunIdFilterInSearchTraces",
    false
  );

  // Check if trace is already associated with the same experiment
  const traceInfo = trace.info as ModelTraceInfoV3;
  const isTraceInExperiment =
    traceInfo.trace_location?.type === "MLFLOW_EXPERIMENT" &&
    traceInfo.trace_location.mlflow_experiment?.experiment_id === experimentId;

  if (isTraceInExperiment) {
    // Trace is already in the correct experiment
    if (runId && traceInfo.trace_id) {
      // Just link it to the run using trace_id
      await linkTracesToRun(runId, [traceInfo.trace_id]);
    }
    return trace;
  }

  if (useTraceInputLinking) {
    // Safe mode: link existing traces to runs without copying
    if (runId && traceInfo.trace_id) {
      await linkTracesToRun(runId, [traceInfo.trace_id]);
    }
    return trace;
  } else {
    // Default mode: copy the trace to the target experiment
    const copiedTraces = await copyTracesToRun([trace], experimentId, runId);
    return copiedTraces[0];
  }
};

// Function to copy traces to experiment/run (uses reviewAppQueries.tsx createTrace logic)
const copyTracesToRun = async (
  traces: ModelTrace[],
  experimentId: string,
  runId?: string
): Promise<ModelTrace[]> => {
  // Update trace metadata to point to the new run
  const updatedTraces = traces.map((trace) => {
    const traceInfo = trace.info as ModelTraceInfoV3;
    return {
      ...trace,
      info: {
        ...traceInfo,
        trace_metadata: {
          ...traceInfo.trace_metadata,
          ...(runId && { "mlflow.sourceRun": runId }),
        },
      },
    };
  });

  // Link all traces to the run if runId is provided
  if (runId) {
    const traceIds = updatedTraces
      .map((trace) => (trace.info as ModelTraceInfoV3).trace_id)
      .filter((id): id is string => Boolean(id));
    if (traceIds.length > 0) {
      await linkTracesToRun(runId, traceIds);
    }
  }

  return updatedTraces;
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

// Hook to add dataset to labeling session (mirrors Python add_dataset method)
export const useAddDatasetToLabelingSession = (experimentId: string) => {
  const queryClient = useQueryClient();
  const { reviewApp } = useGetReviewApp(experimentId);

  return useMutation({
    mutationFn: async (params: {
      labelingSessionId: string;
      datasetId: string;
      recordIds?: string[];
    }) => {
      const { labelingSessionId, datasetId, recordIds } = params;

      // Validate inputs (mirror Python assertions)
      if (typeof datasetId !== "string") {
        throw new Error("`datasetId` must be a string");
      }

      if (recordIds && !recordIds.every((id) => typeof id === "string")) {
        throw new Error("`recordIds` must be a list of strings");
      }

      if (!reviewApp?.review_app_id) {
        throw new Error("Review app ID is required");
      }

      // Get the labeling session to check assigned users and agent
      const labelingSessions = await listLabelingSessions(
        reviewApp.review_app_id
      );
      const labelingSession = labelingSessions.find(
        (s) => s.labeling_session_id === labelingSessionId
      );

      if (!labelingSession) {
        throw new Error(`Labeling session ${labelingSessionId} not found`);
      }

      // Add users to dataset if assigned users exist (mirrors Python logic)
      // Note: This would need to be implemented with proper workspace API calls
      if (
        labelingSession.assigned_users &&
        labelingSession.assigned_users.length > 0
      ) {
        // TODO: Implement actual Unity Catalog grants update
        // await addUsersToDataset(labelingSession.assigned_users, datasetName);
      }

      // Get dataset records (no need to call getDatasetId since we already have it)
      const allDatasetRecords = await listDatasetRecords(datasetId);
      const datasetRecordsMap = new Map<string, DatasetRecord>();
      allDatasetRecords.forEach((record) => {
        if (record.dataset_record_id) {
          datasetRecordsMap.set(record.dataset_record_id, record);
        }
      });

      // Get existing record IDs in the session (mirrors Python logic)
      const existingItems = await listLabelingSessionItems(
        reviewApp.review_app_id,
        labelingSessionId
      );
      const existingRecordIds = new Set<string>();

      existingItems.forEach((item) => {
        if (item.source?.dataset_record?.dataset_record_id) {
          existingRecordIds.add(item.source.dataset_record.dataset_record_id);
        }
      });

      // Determine which records to add (mirrors Python set operations)
      const recordIdsToConsider =
        recordIds || Array.from(datasetRecordsMap.keys());
      const recordIdsToAdd = recordIdsToConsider.filter(
        (id) => !existingRecordIds.has(id)
      );

      if (recordIdsToAdd.length === 0) {
        return; // Nothing to add
      }

      // Handle different scenarios based on whether session has an agent (mirrors Python logic)
      if (labelingSession.agent?.agent_name) {
        // Session has an agent - add dataset records directly
        await batchCreateItemsInLabelingSession(
          reviewApp.review_app_id,
          labelingSessionId,
          {
            datasetId,
            datasetRecordIds: recordIdsToAdd,
          }
        );
      } else {
        // Session has no agent - need to get traces from dataset records
        const traces: ModelTrace[] = []; // Using full ModelTrace objects

        for (const recordId of recordIdsToAdd) {
          const record = datasetRecordsMap.get(recordId);

          if (!record?.source?.trace?.trace_id) {
            throw new Error(
              `Record ${recordId} has no trace and this session has no agent. ` +
                "Either provide records that have associated traces or " +
                "add an agent to this session to generate responses"
            );
          }

          // Get the full trace using MLflow API (following useGetTraceV3 pattern)
          try {
            const [traceInfoResponse, traceData] = await Promise.all([
              MlflowService.getExperimentTraceInfoV3(
                record.source.trace.trace_id
              ),
              MlflowService.getExperimentTraceData(
                record.source.trace.trace_id
              ),
            ]);

            if (traceInfoResponse?.trace?.trace_info && traceData) {
              // Convert to ModelTrace format
              const modelTrace: ModelTrace = {
                info: traceInfoResponse.trace.trace_info,
                data: traceData,
              };
              traces.push(modelTrace);
            }
          } catch (error) {
            throw new Error(
              `Failed to get trace ${record.source.trace.trace_id}: ${error}`
            );
          }
        }

        // Log traces to experiment and get trace IDs (mirrors Python logic)
        const traceIds: string[] = [];
        for (const trace of traces) {
          const loggedTrace = await logTraceToExperiment(
            trace,
            experimentId,
            labelingSession.mlflow_run_id
          );
          const traceId = (loggedTrace.info as ModelTraceInfoV3).trace_id;
          if (traceId) {
            traceIds.push(traceId);
          }
        }

        // Add traces to labeling session
        await batchCreateItemsInLabelingSession(
          reviewApp.review_app_id,
          labelingSessionId,
          {
            traceIds,
          }
        );
      }

      return { recordsAdded: recordIdsToAdd.length };
    },
    onSuccess: () => {
      // Invalidate and refetch labeling session items
      queryClient.invalidateQueries({
        queryKey: [
          "labelingSessionItems",
          "hydrated",
          reviewApp?.review_app_id,
        ],
      });
    },
  });
};

// Export types for use in other components
export type {
  ReviewApp,
  LabelingSession,
  HydratedLabelingSession,
  LabelingSchema,
  Agent,
  Item,
  HydratedItem,
  ModelTraceInfoV3,
};
