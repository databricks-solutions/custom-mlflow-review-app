import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { LoadingState } from "@/components/LoadingState";
import { useQueryClient } from "@tanstack/react-query";
import {
  useAppManifest,
  useLabelingSession,
  useLabelingItems,
  useUpdateLabelingItem,
  useTrace,
  useRendererName,
  useLabelSchemas,
  queryKeys,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";
import { getRendererComponent } from "@/components/session-renderer/renderers";
import { TraceData, Assessment, SchemaAssessments } from "@/types/renderers";
import { combineSchemaWithAssessments, filterByType } from "@/utils/schema-assessment-utils";

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

  // Data fetching - get review app from manifest
  const { data: manifest, isLoading: isLoadingManifest } = useAppManifest();
  const reviewApp = manifest?.review_app;
  const { data: session } = useLabelingSession(
    sessionId,
    !!sessionId
  );

  // Fetch all available schemas to match with session references
  const { data: allSchemas } = useLabelSchemas();

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
    const itemData: Record<string, string | undefined> = {};
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
    // Don't reset assessments here - let the useEffect handle loading from trace data
  };

  // Load assessments from trace data when trace changes
  useEffect(() => {
    if (traceSummary?.info?.assessments && Array.isArray(traceSummary.info.assessments)) {
      const assessmentMap = new Map<string, Assessment>();
      
      console.log('[DEBUG] Loading assessments from trace:', traceSummary.info.assessments);
      
      // Group assessments by name and type, keeping only the latest one
      const latestAssessments = new Map<string, Assessment>();
      
      for (const assessment of traceSummary.info.assessments) {
        const key = `${assessment.name}_${assessment.type}`;
        const existing = latestAssessments.get(key);
        
        // Keep the latest assessment (you could also compare timestamps if available)
        if (!existing || (assessment.assessment_id && (!existing.assessment_id || assessment.assessment_id > existing.assessment_id))) {
          latestAssessments.set(key, assessment);
        }
      }
      
      console.log('[DEBUG] Latest assessments:', Array.from(latestAssessments.entries()));
      
      // Now map by name only (since schema name is unique)
      for (const assessment of latestAssessments.values()) {
        assessmentMap.set(assessment.name, assessment);
      }
      
      console.log('[DEBUG] Final assessment map:', Array.from(assessmentMap.entries()));
      setAssessments(assessmentMap);
    }
  }, [traceSummary]);

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

  if (isLoadingItems || isLoadingTrace || isLoadingManifest) {
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

  // Compute schema assessments from session schemas and trace assessments
  const schemaAssessments: SchemaAssessments | undefined = session?.labeling_schemas && allSchemas ? (() => {
    // Map session schema references to full schema objects
    const sessionSchemas = session.labeling_schemas
      .map(ref => allSchemas.find(schema => schema.name === ref.name))
      .filter(Boolean) as any[];
    
    const combinedSchemas = combineSchemaWithAssessments(sessionSchemas, traceSummary.info.assessments);
    
    return {
      feedback: filterByType(combinedSchemas, 'FEEDBACK'),
      expectations: filterByType(combinedSchemas, 'EXPECTATION'),
    };
  })() : undefined;

  return (
    <div className="h-screen flex flex-col">
      {/* Header - Fixed */}
      <div className="flex-shrink-0 border-b bg-background p-6">
        <div className="container mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-4 mb-2">
              {!hideNavigation && (
                <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <h1 className="text-2xl font-bold">{session?.name || "Labeling Session"}</h1>
            </div>
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
                      idx === currentItemIndex
                        ? "bg-blue-500"
                        : item.state === "COMPLETED"
                          ? "bg-green-500"
                          : item.state === "SKIPPED"
                            ? "bg-yellow-500"
                            : "bg-gray-300"
                    }`}
                    onClick={() => setCurrentItemIndex(idx)}
                    title={`Item ${idx + 1} - ${item.state}${idx === currentItemIndex ? " (current)" : ""}`}
                  />
                ))}
              </div>
            </div>

            {/* Navigation buttons */}
            <div className="flex items-center gap-3">
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

              <p className="text-xs text-muted-foreground">
                {currentItemIndex + 1} of {items.length}
              </p>

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
      </div>

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6">
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
            schemaAssessments={schemaAssessments}
          />
        </div>
      </div>
    </div>
  );
}
