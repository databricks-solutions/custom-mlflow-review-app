/**
 * React Query hooks using the auto-generated API client.
 *
 * This module provides React Query hooks that use the auto-generated
 * FastAPI client for type-safe API operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { ReviewApp, LabelingSession, LabelingItem } from "@/types/renderers";
import { SimplifiedApiService, type LabelingSchema } from "@/fastapi_client";

// Query Keys Factory
export const queryKeys = {
  manifest: () => ["manifest"] as const,
  config: () => ["config"] as const,
  user: () => ["user"] as const,
  userRole: () => ["user", "role"] as const,

  reviewApps: {
    all: () => ["review-apps"] as const,
    list: (filter?: string) => ["review-apps", "list", { filter }] as const,
    detail: (id: string) => ["review-apps", id] as const,
  },

  labelingSessions: {
    all: () => ["labeling-sessions"] as const,
    list: () => ["labeling-sessions", "list"] as const,
    detail: (sessionId: string) => ["labeling-sessions", sessionId] as const,
    analysis: (reviewAppId: string, sessionId: string) =>
      ["labeling-sessions", reviewAppId, sessionId, "analysis"] as const,
    analysisStatus: (reviewAppId: string, sessionId: string) =>
      ["labeling-sessions", reviewAppId, sessionId, "analysis", "status"] as const,
  },

  labelingItems: {
    list: (reviewAppId: string, sessionId: string) =>
      ["labeling-items", reviewAppId, sessionId] as const,
  },

  traces: {
    all: () => ["traces"] as const,
    search: (params: Record<string, unknown>) => ["traces", "search", params] as const,
    detail: (traceId: string) => ["traces", traceId] as const,
    detailWithRun: (traceId: string, runId: string) => ["traces", traceId, "run", runId] as const,
    metadata: (traceId: string) => ["traces", traceId, "metadata"] as const,
  },

  experiments: {
    detail: (id: string) => ["experiments", id] as const,
    summary: (id: string) => ["experiments", id, "summary"] as const,
    analysisStatus: (id: string) => ["experiments", id, "analysis", "status"] as const,
  },

  runs: {
    detail: (id: string) => ["runs", id] as const,
  },

  labelSchemas: {
    all: () => ["label-schemas"] as const,
    list: () => ["label-schemas", "list"] as const,
  },

  renderers: {
    name: (runId: string) => ["renderers", "name", runId] as const,
  },
};

// Unified Manifest (contains user, workspace, config, and review app info)
export function useAppManifest() {
  return useQuery({
    queryKey: queryKeys.manifest(),
    queryFn: async () => {
      const response = await fetch("/api/manifest");
      if (!response.ok) {
        throw new Error("Failed to fetch app manifest");
      }
      return response.json();
    },
    retry: false, // Don't retry if auth fails
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

// Configuration (from manifest)
export function useConfig() {
  const { data: manifest, ...rest } = useAppManifest();
  return {
    data: manifest?.config,
    ...rest
  };
}

// User (from manifest)
export function useCurrentUser() {
  const { data: manifest, ...rest } = useAppManifest();
  return {
    data: manifest?.user,
    ...rest
  };
}

export function useUserRole() {
  // Get user role from the manifest
  const { data: manifest, ...rest } = useAppManifest();
  
  // Transform the user data to match the old user-role response format
  // for backward compatibility
  const roleData = manifest?.user ? {
    username: manifest.user.userName,
    role: manifest.user.role || 'sme',
    is_developer: manifest.user.is_developer || false,
    can_access_dev_pages: manifest.user.can_access_dev_pages || false,
  } : undefined;
  
  return {
    data: roleData,
    ...rest
  };
}

// Review Apps
export function useReviewApps(filter?: string) {
  return useQuery({
    queryKey: queryKeys.reviewApps.list(filter),
    queryFn: () =>
      apiClient.api.listReviewApps({
        filter,
      }),
  });
}


export function useCreateReviewApp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewApp: Partial<ReviewApp>) => apiClient.api.createReviewApp({ reviewApp }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reviewApps.all() });
      toast.success("Review app created successfully");
    },
  });
}

export function useUpdateReviewApp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reviewAppId,
      reviewApp,
      updateMask,
    }: {
      reviewAppId: string;
      reviewApp: Partial<ReviewApp>;
      updateMask: string;
    }) => apiClient.api.updateReviewApp({ reviewAppId, reviewApp, updateMask }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviewApps.detail(variables.reviewAppId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviewApps.all() });
      toast.success("Review app updated successfully");
    },
  });
}

// Labeling Sessions
export function useLabelingSessions(enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.list(),
    queryFn: () => SimplifiedApiService.listLabelingSessionsApiLabelingSessionsGet(),
    enabled,
  });
}

export function useLabelingSession(sessionId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.detail(sessionId),
    queryFn: () => SimplifiedApiService.getLabelingSessionApiLabelingSessionsLabelingSessionIdGet(sessionId),
    enabled: enabled && !!sessionId,
  });
}

export function useCreateLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (session: LabelingSession) => 
      SimplifiedApiService.createLabelingSessionApiLabelingSessionsPost(session),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(),
      });
      toast.success("Labeling session created successfully");
    },
  });
}

export function useUpdateLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      session,
      updateMask,
    }: {
      sessionId: string;
      session: LabelingSession;
      updateMask: string;
    }) => SimplifiedApiService.updateLabelingSessionApiLabelingSessionsLabelingSessionIdPatch(
        sessionId, 
        updateMask, 
        session
      ),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.detail(variables.sessionId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(),
      });
      toast.success("Labeling session updated successfully");
    },
  });
}

export function useDeleteLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId }: { sessionId: string }) =>
      SimplifiedApiService.deleteLabelingSessionApiLabelingSessionsLabelingSessionIdDelete(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(),
      });
      toast.success("Labeling session deleted successfully");
    },
  });
}

// Labeling Items
export function useLabelingItems(reviewAppId: string, sessionId: string, enabled = true) {
  // Debug logging to track which components are calling this hook
  console.log(
    `[HOOK-DEBUG] useLabelingItems called for session ${sessionId.slice(0, 8)} with enabled: ${enabled}`
  );

  return useQuery({
    queryKey: queryKeys.labelingItems.list(reviewAppId, sessionId),
    queryFn: () => {
      console.log(`[API-DEBUG] Making API call for session ${sessionId.slice(0, 8)}`);
      return apiClient.api.listLabelingItems({ reviewAppId, sessionId });
    },
    enabled: enabled && !!reviewAppId && !!sessionId,
  });
}

export function useUpdateLabelingItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reviewAppId,
      sessionId,
      itemId,
      item,
      updateMask,
    }: {
      reviewAppId: string;
      sessionId: string;
      itemId: string;
      item: Partial<LabelingItem>;
      updateMask: string;
    }) => apiClient.api.updateLabelingItem({ reviewAppId, sessionId, itemId, item, updateMask }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingItems.list(variables.reviewAppId, variables.sessionId),
      });
      toast.success("Labels saved successfully");
    },
  });
}

export function useDeleteLabelingItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reviewAppId,
      sessionId,
      itemId,
    }: {
      reviewAppId: string;
      sessionId: string;
      itemId: string;
    }) => apiClient.api.deleteLabelingItem({ reviewAppId, sessionId, itemId }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingItems.list(variables.reviewAppId, variables.sessionId),
      });
      toast.success("Trace removed from session successfully");
    },
  });
}

// Traces
export function useSearchTraces(params: Record<string, unknown>, enabled = true) {
  return useQuery({
    queryKey: queryKeys.traces.search(params),
    queryFn: () => apiClient.api.searchTraces(params),
    enabled,
  });
}

export function useTrace(traceId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.traces.detail(traceId),
    queryFn: () => apiClient.api.getTrace({ traceId }),
    enabled: enabled && !!traceId,
    staleTime: 5 * 60 * 1000, // 5 minutes - match prefetch staleTime
  });
}

export function useTraceMetadata(traceId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.traces.metadata(traceId),
    queryFn: () => apiClient.api.getTraceMetadata({ traceId }),
    enabled: enabled && !!traceId,
  });
}

export function useLinkTracesToRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ runId, traceIds }: { runId: string; traceIds: string[] }) =>
      apiClient.api.linkTracesToRun({ runId, traceIds }),
    onSuccess: (data, variables) => {
      // Invalidate trace searches
      queryClient.invalidateQueries({ queryKey: queryKeys.traces.all() });
      toast.success(`Successfully linked ${variables.traceIds.length} traces to run`);
    },
  });
}

// MLflow

export function useExperimentSummary(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experiments.summary(experimentId),
    queryFn: async () => {
      const response = await fetch(`/api/experiment-summary/${experimentId}`);
      if (!response.ok) {
        throw new Error("Failed to fetch experiment summary");
      }
      return response.json();
    },
    enabled: enabled && !!experimentId,
    staleTime: 10 * 60 * 1000, // 10 minutes - summaries don't change often
  });
}

export function useRun(runId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.runs.detail(runId),
    queryFn: () => apiClient.api.getRun({ runId }),
    enabled: enabled && !!runId,
  });
}

// Custom hook to get renderer name from MLflow run tags
export function useRendererName(runId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.renderers.name(runId),
    queryFn: async () => {
      const runData = await apiClient.api.getRun({ runId });
      const rendererName = runData?.run?.data?.tags?.find(
        (tag: { key?: string; value?: string }) => tag.key === "mlflow.customRenderer"
      )?.value;
      return { rendererName, runData };
    },
    enabled: enabled && !!runId,
    select: (data) => ({
      rendererName: data.rendererName,
      runData: data.runData,
    }),
  });
}

export function useUpdateRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      run_id: string;
      status?: string;
      end_time?: number;
      tags?: Array<{ key: string; value: string }>;
    }) => apiClient.api.updateRun(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.detail(variables.run_id) });
    },
    onError: (error: Error) => {
      toast.error(`Failed to update run: ${error.message}`);
    },
  });
}

// Helper hook specifically for setting renderer tag
export function useSetRendererTag() {
  const queryClient = useQueryClient();
  const updateRun = useUpdateRun();

  return useMutation({
    mutationFn: ({ runId, rendererName }: { runId: string; rendererName: string }) =>
      updateRun.mutateAsync({
        run_id: runId,
        tags: [{ key: "mlflow.customRenderer", value: rendererName }],
      }),
    onSuccess: (data, { runId }) => {
      // Invalidate renderer name queries to refetch with new value
      queryClient.invalidateQueries({
        queryKey: queryKeys.renderers.name(runId),
      });
    },
  });
}

export function useCreateRun() {
  // const queryClient = useQueryClient(); // Not currently used

  return useMutation({
    mutationFn: (runData: Record<string, unknown>) => apiClient.api.createRun(runData),
    onSuccess: () => {
      toast.success("Run created successfully");
    },
  });
}

// Analysis hooks
export function useSessionAnalysis(reviewAppId: string, sessionId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.analysis(reviewAppId, sessionId),
    queryFn: () => apiClient.api.getSessionAnalysis({ reviewAppId, sessionId }),
    enabled: enabled && !!reviewAppId && !!sessionId,
    retry: 1,
  });
}

export function useAnalysisStatus(reviewAppId: string, sessionId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.analysisStatus(reviewAppId, sessionId),
    queryFn: () => apiClient.api.getAnalysisStatus({ reviewAppId, sessionId }),
    enabled: enabled && !!reviewAppId && !!sessionId,
    retry: 1,
  });
}

export function useTriggerSessionAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reviewAppId,
      sessionId,
      includeAiInsights = true,
      modelEndpoint = "databricks-claude-sonnet-4",
    }: {
      reviewAppId: string;
      sessionId: string;
      includeAiInsights?: boolean;
      modelEndpoint?: string;
    }) =>
      apiClient.api.triggerSessionAnalysis({
        reviewAppId,
        sessionId,
        include_ai_insights: includeAiInsights,
        model_endpoint: modelEndpoint,
      }),
    onSuccess: (data, variables) => {
      // Invalidate analysis queries to refresh
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.analysis(variables.reviewAppId, variables.sessionId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.analysisStatus(
          variables.reviewAppId,
          variables.sessionId
        ),
      });
    },
  });
}

// Experiment Analysis hooks
export function useExperimentAnalysisStatus(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experiments.analysisStatus(experimentId),
    queryFn: () =>
      apiClient.api.getAnalysisStatusApiExperimentSummaryStatusExperimentIdGet(experimentId),
    enabled: enabled && !!experimentId,
    refetchInterval: (query) => {
      // Only poll if there's an active task running
      const status = query.state.data?.status;
      return status === 'running' || status === 'pending' ? 3000 : false;
    },
    refetchIntervalInBackground: false,
  });
}

export function useTriggerExperimentAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      experimentId,
      focus = "comprehensive",
      traceSampleSize = 50,
      modelEndpoint = "databricks-claude-sonnet-4",
    }: {
      experimentId: string;
      focus?: string;
      traceSampleSize?: number;
      modelEndpoint?: string;
    }) =>
      apiClient.api.triggerAnalysisApiExperimentSummaryTriggerAnalysisPost({
        experiment_id: experimentId,
        focus,
        trace_sample_size: traceSampleSize,
        model_endpoint: modelEndpoint,
      }),
    onSuccess: (data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.experiments.analysisStatus(variables.experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.experiments.summary(variables.experimentId),
      });
    },
  });
}

// MLflow Feedback and Expectation Mutations
// These mutations are used to log and update feedback and expectations on traces

/**
 * Hook to log feedback on a trace
 */
export function useLogFeedbackMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      traceId,
      name,
      value,
      rationale,
    }: {
      traceId: string;
      name: string;
      value: string | number | boolean | Array<string> | Record<string, unknown>;
      rationale?: string;
    }) =>
      apiClient.api.logTraceFeedback({
        traceId,
        name,
        value,
        rationale,
      }),
    onSuccess: (data, variables) => {
      // Invalidate trace-related queries to refresh feedback
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.detail(variables.traceId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.metadata(variables.traceId),
      });
    },
    onError: (error: Error) => {
      console.error("Failed to log feedback:", error);
      toast.error("Failed to save feedback");
    },
  });
}

/**
 * Hook to update existing feedback on a trace
 */
export function useUpdateFeedbackMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      traceId,
      assessmentId,
      value,
      rationale,
    }: {
      traceId: string;
      assessmentId: string;
      value: string | number | boolean | Array<string> | Record<string, unknown>;
      rationale?: string;
    }) =>
      apiClient.api.updateTraceFeedback({
        traceId,
        assessment_id: assessmentId,
        value,
        rationale,
      }),
    onSuccess: (data, variables) => {
      // Invalidate trace-related queries to refresh feedback
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.detail(variables.traceId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.metadata(variables.traceId),
      });
    },
    onError: (error: Error) => {
      console.error("Failed to update feedback:", error);
      toast.error("Failed to update feedback");
    },
  });
}

/**
 * Hook to log expectation on a trace
 */
export function useLogExpectationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      traceId,
      name,
      value,
      rationale,
    }: {
      traceId: string;
      name: string;
      value: string | number | boolean | Array<string> | Record<string, unknown>;
      rationale?: string;
    }) =>
      apiClient.api.logTraceExpectation({
        traceId,
        name,
        value,
        rationale,
      }),
    onSuccess: (data, variables) => {
      // Invalidate trace-related queries to refresh expectations
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.detail(variables.traceId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.metadata(variables.traceId),
      });
    },
    onError: (error: Error) => {
      console.error("Failed to log expectation:", error);
      toast.error("Failed to save expectation");
    },
  });
}

/**
 * Hook to update existing expectation on a trace
 */
export function useUpdateExpectationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      traceId,
      assessmentId,
      value,
      rationale,
    }: {
      traceId: string;
      assessmentId: string;
      value: string | number | boolean | Array<string> | Record<string, unknown>;
      rationale?: string;
    }) =>
      apiClient.api.updateTraceExpectation({
        traceId,
        assessment_id: assessmentId,
        value,
        rationale,
      }),
    onSuccess: (data, variables) => {
      // Invalidate trace-related queries to refresh expectations
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.detail(variables.traceId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.traces.metadata(variables.traceId),
      });
    },
    onError: (error: Error) => {
      console.error("Failed to update expectation:", error);
      toast.error("Failed to update expectation");
    },
  });
}

// Label Schemas
export function useLabelSchemas(enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelSchemas.list(),
    queryFn: () => SimplifiedApiService.listLabelSchemasApiLabelSchemasGet(),
    enabled,
  });
}

export function useCreateLabelSchema() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (schema: LabelingSchema) => 
      SimplifiedApiService.createLabelSchemaApiLabelSchemasPost(schema),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelSchemas.list(),
      });
      toast.success("Label schema created successfully");
    },
    onError: (error: Error) => {
      toast.error(`Failed to create schema: ${error.message}`);
    },
  });
}

export function useUpdateLabelSchema() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      schemaName,
      schema,
    }: {
      schemaName: string;
      schema: LabelingSchema;
    }) => 
      SimplifiedApiService.updateLabelSchemaApiLabelSchemasSchemaNamePatch(
        schemaName,
        schema
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelSchemas.list(),
      });
      toast.success("Label schema updated successfully");
    },
    onError: (error: Error) => {
      toast.error(`Failed to update schema: ${error.message}`);
    },
  });
}

export function useDeleteLabelSchema() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ schemaName }: { schemaName: string }) => 
      SimplifiedApiService.deleteLabelSchemaApiLabelSchemasSchemaNameDelete(schemaName),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelSchemas.list(),
      });
      toast.success("Label schema deleted successfully");
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete schema: ${error.message}`);
    },
  });
}
