/**
 * React Query hooks using the auto-generated API client.
 *
 * This module provides React Query hooks that use the auto-generated
 * FastAPI client for type-safe API operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";

// Query Keys Factory
export const queryKeys = {
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
    list: (reviewAppId: string) => ["labeling-sessions", reviewAppId] as const,
    detail: (reviewAppId: string, sessionId: string) =>
      ["labeling-sessions", reviewAppId, sessionId] as const,
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
    search: (params: any) => ["traces", "search", params] as const,
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

  renderers: {
    name: (runId: string) => ["renderers", "name", runId] as const,
  },
};

// Configuration
export function useConfig() {
  return useQuery({
    queryKey: queryKeys.config(),
    queryFn: () => apiClient.api.getConfig(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// User
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.user(),
    queryFn: () => apiClient.api.getCurrentUser(),
    retry: false, // Don't retry if auth fails
  });
}

export function useUserRole() {
  return useQuery({
    queryKey: queryKeys.userRole(),
    queryFn: async () => {
      // Make a direct fetch call since the API client may not be generated yet
      const response = await fetch('/api/auth/user-role');
      if (!response.ok) {
        throw new Error('Failed to fetch user role');
      }
      return response.json();
    },
    retry: false, // Don't retry if auth fails
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

// Review Apps
export function useReviewApps(filter?: string) {
  return useQuery({
    queryKey: queryKeys.reviewApps.list(filter),
    queryFn: () => apiClient.api.listReviewApps({ 
      filter,
      pageSize: filter ? 10 : 500 // Use smaller page size when filtering since we expect 1 result
    }),
  });
}


export function useCurrentReviewApp() {
  return useQuery({
    queryKey: ['current-review-app'],
    queryFn: async () => {
      const result = await apiClient.api.getCurrentReviewApp();
      return result;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes since experiment:review_app is 1:1
  });
}

export function useCreateReviewApp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewApp: any) => apiClient.api.createReviewApp({ reviewApp }),
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
      reviewApp: any;
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
export function useLabelingSessions(reviewAppId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.list(reviewAppId),
    queryFn: () => apiClient.api.listLabelingSessions({ reviewAppId }),
    enabled: enabled && !!reviewAppId,
  });
}

export function useLabelingSession(reviewAppId: string, sessionId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.labelingSessions.detail(reviewAppId, sessionId),
    queryFn: () => apiClient.api.getLabelingSession({ reviewAppId, sessionId }),
    enabled: enabled && !!reviewAppId && !!sessionId,
  });
}

export function useCreateLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewAppId, session }: { reviewAppId: string; session: any }) =>
      apiClient.api.createLabelingSession({ reviewAppId, session }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(variables.reviewAppId),
      });
      toast.success("Labeling session created successfully");
    },
  });
}

export function useUpdateLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reviewAppId,
      sessionId,
      session,
    }: {
      reviewAppId: string;
      sessionId: string;
      session: any;
    }) => apiClient.api.updateLabelingSession({ reviewAppId, sessionId, session }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.detail(variables.reviewAppId, variables.sessionId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(variables.reviewAppId),
      });
      toast.success("Labeling session updated successfully");
    },
  });
}

export function useDeleteLabelingSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewAppId, sessionId }: { reviewAppId: string; sessionId: string }) =>
      apiClient.api.deleteLabelingSession({ reviewAppId, sessionId }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingSessions.list(variables.reviewAppId),
      });
      toast.success("Labeling session deleted successfully");
    },
  });
}

// Labeling Items
export function useLabelingItems(reviewAppId: string, sessionId: string, enabled = true) {
  // Debug logging to track which components are calling this hook
  console.log(`[HOOK-DEBUG] useLabelingItems called for session ${sessionId.slice(0, 8)} with enabled: ${enabled}`);
  
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
      item: any;
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
export function useSearchTraces(params: any, enabled = true) {
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
export function useExperiment(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experiments.detail(experimentId),
    queryFn: () => apiClient.api.getExperiment({ experimentId }),
    enabled: enabled && !!experimentId,
  });
}

export function useExperimentSummary(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experiments.summary(experimentId),
    queryFn: async () => {
      const response = await fetch(`/api/experiment-summary/${experimentId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch experiment summary');
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
        (tag) => tag.key === 'mlflow.customRenderer'
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
    mutationFn: (data: { run_id: string; status?: string; end_time?: number; tags?: Array<{key: string; value: string}> }) =>
      apiClient.api.updateRun(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.detail(variables.run_id) });
    },
    onError: (error: any) => {
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
        tags: [{ key: 'mlflow.customRenderer', value: rendererName }]
      }),
    onSuccess: (data, { runId }) => {
      // Invalidate renderer name queries to refetch with new value
      queryClient.invalidateQueries({
        queryKey: queryKeys.renderers.name(runId)
      });
    },
  });
}

export function useCreateRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runData: any) => apiClient.api.createRun(runData),
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
    mutationFn: ({ reviewAppId, sessionId, includeAiInsights = true, modelEndpoint = 'databricks-claude-sonnet-4' }: {
      reviewAppId: string;
      sessionId: string;
      includeAiInsights?: boolean;
      modelEndpoint?: string;
    }) => apiClient.api.triggerSessionAnalysis({
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
        queryKey: queryKeys.labelingSessions.analysisStatus(variables.reviewAppId, variables.sessionId),
      });
    },
  });
}

// Experiment Analysis hooks
export function useExperimentAnalysisStatus(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experiments.analysisStatus(experimentId),
    queryFn: () => apiClient.api.getAnalysisStatusExperimentSummaryStatusExperimentIdGet(experimentId),
    enabled: enabled && !!experimentId,
    refetchInterval: 3000, // Poll every 3 seconds by default
    refetchIntervalInBackground: false,
  });
}

export function useTriggerExperimentAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, focus = 'comprehensive', traceSampleSize = 50, modelEndpoint = 'databricks-claude-sonnet-4' }: {
      experimentId: string;
      focus?: string;
      traceSampleSize?: number;
      modelEndpoint?: string;
    }) => apiClient.api.triggerAnalysisExperimentSummaryTriggerAnalysisPost({
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

