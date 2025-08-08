/**
 * Shared hooks for MLflow logging operations
 * Used across multiple renderer components
 */

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

/**
 * Hook for logging feedback to MLflow
 */
export function useLogFeedbackMutation() {
  return useMutation({
    mutationFn: async ({
      traceId,
      feedbackKey,
      feedbackValue,
      rationale,
    }: {
      traceId: string;
      feedbackKey: string;
      feedbackValue: any;
      rationale?: string;
    }) => {
      return apiClient.api.logFeedback({
        logFeedbackRequest: {
          trace_id: traceId,
          feedback_key: feedbackKey,
          feedback_value: feedbackValue,
          rationale,
        },
      });
    },
    onError: (error: any) => {
      console.error("Failed to log feedback:", error);
      toast.error("Failed to save feedback");
    },
  });
}

/**
 * Hook for logging expectations to MLflow
 */
export function useLogExpectationMutation() {
  return useMutation({
    mutationFn: async ({
      traceId,
      expectationKey,
      expectationValue,
      rationale,
    }: {
      traceId: string;
      expectationKey: string;
      expectationValue: any;
      rationale?: string;
    }) => {
      return apiClient.api.logExpectation({
        logExpectationRequest: {
          trace_id: traceId,
          expectation_key: expectationKey,
          expectation_value: expectationValue,
          rationale,
        },
      });
    },
    onError: (error: any) => {
      console.error("Failed to log expectation:", error);
      toast.error("Failed to save expectation");
    },
  });
}
