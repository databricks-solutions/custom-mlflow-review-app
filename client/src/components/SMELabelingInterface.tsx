import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
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
import { TraceData } from "@/types/renderers";

interface SMELabelingInterfaceProps {
  sessionId: string;
  hideNavigation?: boolean;
}

export function SMELabelingInterface({ sessionId, hideNavigation = false }: SMELabelingInterfaceProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [labels, setLabels] = useState<Record<string, any>>({});

  // Data fetching - use current review app instead of taking it as a prop
  const { data: reviewApp, isLoading: isLoadingReviewApp } = useCurrentReviewApp();
  const { data: session } = useLabelingSession(reviewApp?.review_app_id || "", sessionId, !!reviewApp?.review_app_id && !!sessionId);
  
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
    (currentItem?.source && 'trace_id' in currentItem.source ? currentItem.source.trace_id : null) || "",
    undefined, // Don't pass run_id - fetch trace directly
    !!(currentItem?.source && 'trace_id' in currentItem.source ? currentItem.source.trace_id : null)
  );

  const updateItemMutation = useUpdateLabelingItem();

  // Prefetch next item's trace data
  useEffect(() => {
    if (nextItem?.source?.trace_id) {
      queryClient.prefetchQuery({
        queryKey: queryKeys.traces.detail(nextItem.source.trace_id),
        queryFn: () => apiClient.api.getTrace({ traceId: nextItem.source.trace_id }),
        staleTime: 5 * 60 * 1000, // 5 minutes
      });
    }
  }, [currentItemIndex, nextItem?.source?.trace_id, queryClient]);

  // Get renderer name from MLflow run tags
  const rendererQuery = useRendererName(
    session?.mlflow_run_id || "",
    !!session?.mlflow_run_id
  );
  const rendererName = rendererQuery.data?.rendererName;

  // Get the renderer component based on MLflow run tags
  const RendererComponent = getRendererComponent(rendererName);

  // Pass the update mutation to the renderer for auto-save
  const handleUpdateItem = (itemId: string, updates: { state?: string; labels?: Record<string, any>; comment?: string }) => {
    if (!reviewApp?.review_app_id) {
      throw new Error("Review app ID not available");
    }
    return updateItemMutation.mutateAsync({
      reviewAppId: reviewApp.review_app_id,
      sessionId,
      itemId,
      item: updates,
      updateMask: Object.keys(updates).join(","),
    });
  };

  const handleNavigateToIndex = (index: number) => {
    setCurrentItemIndex(index);
    setLabels({});
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
        <div className="flex items-center gap-2">
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

      {/* Render using custom renderer */}
      <RendererComponent
        item={currentItem}
        traceData={traceData}
        reviewApp={reviewApp}
        session={session!}
        currentIndex={currentItemIndex}
        totalItems={items.length}
        labels={labels}
        onLabelsChange={setLabels}
        onUpdateItem={handleUpdateItem}
        onNavigateToIndex={handleNavigateToIndex}
        isLoading={isLoadingTrace}
        isSubmitting={updateItemMutation.isPending}
      />
    </div>
  );
}