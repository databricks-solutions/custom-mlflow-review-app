import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { LoadingState } from "@/components/LoadingState";
import { useQueryClient } from "@tanstack/react-query";
import {
  useCurrentReviewApp,
  useLabelingSession,
  useLabelingItems,
  useUpdateLabelingItem,
  useTrace,
  useRendererName,
  queryKeys,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";
import { getRendererComponent } from "@/components/session-renderer/renderers";
import { TraceData, Assessment } from "@/types/renderers";

interface SMELabelingInterfaceProps {
  sessionId: string;
  hideNavigation?: boolean;
}

export function SMELabelingInterface({
  sessionId,
  hideNavigation = false,
}: SMELabelingInterfaceProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [assessments, setAssessments] = useState<Map<string, Assessment>>(new Map());

  // Data fetching - use current review app instead of taking it as a prop
  const { data: reviewApp, isLoading: isLoadingReviewApp } = useCurrentReviewApp();
  const { data: session } = useLabelingSession(
    reviewApp?.review_app_id || "",
    sessionId,
    !!reviewApp?.review_app_id && !!sessionId
  );

  // Load items immediately for SME mode
  const { data: itemsData, isLoading: isLoadingItems } = useLabelingItems(
    reviewApp?.review_app_id || "",
    sessionId,
    !!reviewApp?.review_app_id && !!sessionId
  );

  const items = itemsData?.items || [];
  const currentItem = items[currentItemIndex];
  const nextItem = items[currentItemIndex + 1];

  const { data: traceSummary, isLoading: isLoadingTrace } = useTrace(
    (currentItem?.source && "trace_id" in currentItem.source
      ? currentItem.source.trace_id
      : null) || "",
    !!(currentItem?.source && "trace_id" in currentItem.source ? currentItem.source.trace_id : null)
  );

  const updateItemMutation = useUpdateLabelingItem();

  // Prefetch next item's trace data - only after current item has loaded
  useEffect(() => {
    // Only prefetch if:
    // 1. Current trace has finished loading
    // 2. Next item exists and has a trace_id
    // 3. We have a valid trace summary for current item
    if (
      !isLoadingTrace &&
      traceSummary &&
      nextItem?.source?.trace_id &&
      "trace_id" in nextItem.source
    ) {
      console.log(`[PREFETCH] Starting prefetch for next trace: ${nextItem.source.trace_id}`);
      queryClient.prefetchQuery({
        queryKey: queryKeys.traces.detail(nextItem.source.trace_id),
        queryFn: () => apiClient.api.getTrace({ traceId: nextItem.source.trace_id }),
        staleTime: 5 * 60 * 1000, // 5 minutes
      });
    }
  }, [isLoadingTrace, traceSummary, nextItem?.source?.trace_id, queryClient]);

  // Get renderer name from MLflow run tags
  const rendererQuery = useRendererName(session?.mlflow_run_id || "", !!session?.mlflow_run_id);
  const rendererName = rendererQuery.data?.rendererName;

  // Get the renderer component based on MLflow run tags
  const RendererComponent = getRendererComponent(rendererName);

  // Pass the update mutation to the renderer for auto-save
  const handleUpdateItem = (
    itemId: string,
    updates: { state?: string; assessments?: Map<string, Assessment>; comment?: string }
  ) => {
    if (!reviewApp?.review_app_id) {
      throw new Error("Review app ID not available");
    }
    // Only include basic fields that are supported by Databricks API
    const itemData: Record<string, any> = {};
    const updateFields: string[] = [];

    if (updates.state !== undefined) {
      itemData.state = updates.state;
      updateFields.push("state");
    }

    if (updates.comment !== undefined) {
      itemData.comment = updates.comment;
      updateFields.push("comment");
    }

    // Note: assessments are handled separately via MLflow API calls
    // They are not sent as part of the item update

    return updateItemMutation.mutateAsync({
      reviewAppId: reviewApp.review_app_id,
      sessionId,
      itemId,
      item: itemData,
      updateMask: updateFields.join(","),
    });
  };

  const handleNavigateToIndex = (index: number) => {
    setCurrentItemIndex(index);
    setAssessments(new Map());
  };

  const handlePrevious = () => {
    if (currentItemIndex > 0) {
      handleNavigateToIndex(currentItemIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentItemIndex < items.length - 1) {
      handleNavigateToIndex(currentItemIndex + 1);
    }
  };

  const handleNextUnreviewed = () => {
    // Find next item that is not completed or skipped
    for (let i = currentItemIndex + 1; i < items.length; i++) {
      if (items[i].state !== "COMPLETED" && items[i].state !== "SKIPPED") {
        handleNavigateToIndex(i);
        return;
      }
    }
    // If no unreviewed items found after current, look from beginning
    for (let i = 0; i < currentItemIndex; i++) {
      if (items[i].state !== "COMPLETED" && items[i].state !== "SKIPPED") {
        handleNavigateToIndex(i);
        return;
      }
    }
  };

  const hasUnreviewedItems = items.some(
    (item) => item.state !== "COMPLETED" && item.state !== "SKIPPED"
  );

  const getCompletionPercentage = () => {
    const completedItems = items.filter(
      (item) => item.state === "COMPLETED" || item.state === "SKIPPED"
    ).length;
    return Math.round((completedItems / items.length) * 100);
  };

  if (isLoadingItems || isLoadingTrace || isLoadingReviewApp) {
    return <LoadingState />;
  }

  if (items.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>No Items to Label</CardTitle>
            <CardDescription>
              This labeling session doesn't have any items yet. Traces need to be linked to this
              session first.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!hideNavigation && (
              <Button onClick={() => navigate("/")} variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Sessions
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!currentItem || !traceSummary || !reviewApp) {
    return <LoadingState />;
  }

  // Convert trace data to the expected format
  const traceData: TraceData = {
    info: {
      trace_id: traceSummary.info.trace_id,
      request_time: traceSummary.info.request_time,
      execution_duration: traceSummary.info.execution_duration,
      state: traceSummary.info.state,
      assessments: traceSummary.info.assessments,
    },
    spans: traceSummary.data?.spans || [],
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          {!hideNavigation && (
            <Button variant="ghost" size="sm" onClick={() => navigate("/")} className="mb-2">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Sessions
            </Button>
          )}
          <h1 className="text-2xl font-bold">{session?.name || "Labeling Session"}</h1>
          <p className="text-muted-foreground">
            Item {currentItemIndex + 1} of {items.length}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Progress percentage and dots */}
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-light text-muted-foreground">
              {getCompletionPercentage()}%
            </h3>
            <div className="flex items-center gap-1">
              {items.map((item, idx) => (
                <div
                  key={idx}
                  className={`w-2 h-2 rounded-full cursor-pointer ${
                    item.state === "COMPLETED"
                      ? "bg-green-500"
                      : item.state === "SKIPPED"
                        ? "bg-yellow-500"
                        : idx === currentItemIndex
                          ? "bg-blue-500"
                          : "bg-gray-300"
                  }`}
                  onClick={() => setCurrentItemIndex(idx)}
                  title={`Item ${idx + 1} - ${item.state}`}
                />
              ))}
            </div>
          </div>

          {/* Navigation buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevious}
              disabled={currentItemIndex === 0}
              className="p-2"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleNext}
              disabled={currentItemIndex === items.length - 1}
              className="p-2"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>

            {hasUnreviewedItems && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleNextUnreviewed}
                className="flex items-center gap-2"
              >
                Next unreviewed
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Render using custom renderer */}
      <RendererComponent
        item={currentItem}
        traceData={traceData}
        reviewApp={reviewApp}
        session={session!}
        currentIndex={currentItemIndex}
        totalItems={items.length}
        assessments={assessments}
        onAssessmentsChange={setAssessments}
        onUpdateItem={handleUpdateItem}
        onNavigateToIndex={handleNavigateToIndex}
        isLoading={isLoadingTrace}
        isSubmitting={updateItemMutation.isPending}
      />
    </div>
  );
}
