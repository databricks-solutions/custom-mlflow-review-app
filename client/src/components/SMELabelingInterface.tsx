import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { LoadingState } from "@/components/LoadingState";
import {
  useAppManifest,
  useLabelingSession,
  useLabelingItems,
  useUpdateLabelingItem,
  useSessionTraces,
  useRendererName,
  useLabelSchemas,
  useCurrentUser,
} from "@/hooks/api-hooks";
import { getRendererComponent } from "@/components/session-renderer/renderers";
import { Assessment, SchemaAssessments, LabelingSchema, Trace } from "@/types/renderers";
import { Trace as MLflowTrace, Assessment as MLflowAssessment } from "@/types/mlflow-trace";
import { combineSchemaWithAssessments, filterByType } from "@/utils/schema-assessment-utils";

interface SMELabelingInterfaceProps {
  sessionId: string;
  hideNavigation?: boolean;
  initialTraceId?: string;
  reviewAppId?: string;
}

export function SMELabelingInterface({
  sessionId,
  hideNavigation = false,
  initialTraceId,
}: SMELabelingInterfaceProps) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [assessments, setAssessments] = useState<Map<string, Assessment>>(new Map());
  const [hasInitialized, setHasInitialized] = useState(false);
  const [hasAutoCompleted, setHasAutoCompleted] = useState(false);
  const pendingUpdateRef = useRef<string | null>(null);

  // Data fetching - get review app from manifest
  const { data: manifest, isLoading: isLoadingManifest } = useAppManifest();
  const reviewApp = manifest?.review_app;
  const { data: session } = useLabelingSession(sessionId, !!sessionId);
  const { data: currentUser } = useCurrentUser();

  // Fetch all available schemas to match with session references
  const { data: allSchemas } = useLabelSchemas();

  // Load items immediately for SME mode (for state tracking)
  const { data: itemsData, isLoading: isLoadingItems } = useLabelingItems(
    reviewApp?.review_app_id || "",
    sessionId,
    !!reviewApp?.review_app_id && !!sessionId
  );

  const items = itemsData?.items || [];

  // Fetch all traces for the session (for content and assessments)
  const { data: tracesData, isLoading: isLoadingTraces } = useSessionTraces(
    sessionId,
    session?.mlflow_run_id,
    !!sessionId && !!session?.mlflow_run_id
  );

  // Initialize from URL trace parameter if provided
  useEffect(() => {
    if (!hasInitialized && items.length > 0 && initialTraceId) {
      const traceIndex = items.findIndex(
        (item) =>
          item.source && "trace_id" in item.source && item.source.trace_id === initialTraceId
      );
      if (traceIndex !== -1) {
        setCurrentItemIndex(traceIndex);
      }
      setHasInitialized(true);
    } else if (!hasInitialized && items.length > 0) {
      // If no initial trace specified, set the first item's trace in URL
      const firstItem = items[0];
      if (firstItem?.source && "trace_id" in firstItem.source) {
        const newParams = new URLSearchParams(searchParams);
        newParams.set("trace", firstItem.source.trace_id);
        setSearchParams(newParams, { replace: true });
      }
      setHasInitialized(true);
    }
  }, [items, initialTraceId, hasInitialized, searchParams, setSearchParams]);

  const currentItem = items[currentItemIndex];

  // Get the current trace ID from the current item
  const currentTraceId =
    currentItem?.source && "trace_id" in currentItem.source
      ? currentItem.source.trace_id
      : undefined;

  // Find the current trace from the session traces using memoization
  const trace = useMemo(() => {
    if (!tracesData?.traces || !currentTraceId) return null;
    return tracesData.traces.find(
      (t: MLflowTrace) => t.info.trace_id === currentTraceId
    );
  }, [tracesData, currentTraceId]);

  // Check if we've attempted to load traces (to prevent flash)
  const hasAttemptedTraceLoad = tracesData !== undefined || isLoadingTraces;

  const updateItemMutation = useUpdateLabelingItem();

  // No need for prefetching since we already have all traces loaded
  // The useSessionTraces hook loads all traces at once

  // Get renderer name from MLflow run tags
  const rendererQuery = useRendererName(session?.mlflow_run_id || "", !!session?.mlflow_run_id);
  const rendererName = rendererQuery.data?.rendererName;

  // Get the renderer component based on MLflow run tags
  const RendererComponent = getRendererComponent(rendererName);

  // Pass the update mutation to the renderer for auto-save
  const handleUpdateItem = useCallback(
    (
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
    },
    [reviewApp?.review_app_id, sessionId, updateItemMutation]
  );

  const handleNavigateToIndex = (index: number) => {
    setCurrentItemIndex(index);
    // Update URL with the new trace ID
    const newItem = items[index];
    if (newItem?.source && "trace_id" in newItem.source) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("trace", newItem.source.trace_id);
      setSearchParams(newParams, { replace: true });
    }
    // Don't reset assessments here - let the useEffect handle loading from trace data
  };

  // Load assessments from trace data when trace changes
  useEffect(() => {
    // Always start with a fresh map to ensure we don't carry over old assessments
    const assessmentMap = new Map<string, Assessment>();

    // Debug: Log trace change

    if (trace?.info?.assessments && Array.isArray(trace.info.assessments)) {
      // Work with MLflow's native assessment structure
      // Filter assessments to only include those created by the current user
      const userAssessments = trace.info.assessments.filter((mlflowAssessment: MLflowAssessment) => {
        // Check if assessment belongs to current user using MLflow's source structure
        if (!currentUser?.userName && !currentUser?.emails?.[0]) {
          return false;
        }

        const userIdentifiers = [currentUser.userName, ...(currentUser.emails || [])].filter(
          Boolean
        );

        if (!mlflowAssessment.source) {
          return false;
        }

        let sourceString = "";
        if (typeof mlflowAssessment.source === "string") {
          sourceString = mlflowAssessment.source;
        } else if (mlflowAssessment.source?.source_id) {
          sourceString = mlflowAssessment.source.source_id;
        }

        return userIdentifiers.some(
          (identifier) =>
            identifier && sourceString.toLowerCase().includes(identifier.toLowerCase())
        );
      });


      // Group user assessments by name and type, keeping only the latest one
      const latestAssessments = new Map<string, MLflowAssessment>();

      for (const mlflowAssessment of userAssessments) {
        // Use MLflow's name field
        const assessmentName = mlflowAssessment.name;
        const assessmentType = mlflowAssessment.feedback ? "feedback" : "expectation";
        const key = `${assessmentName}_${assessmentType}`;
        const existing = latestAssessments.get(key);

        // Keep the latest assessment (compare by assessment_id or timestamp)
        if (
          !existing ||
          (mlflowAssessment.assessment_id &&
            (!existing.assessment_id || mlflowAssessment.assessment_id > existing.assessment_id))
        ) {
          latestAssessments.set(key, mlflowAssessment);
        }
      }

      // Transform to our internal format for the UI components
      // This transformation happens ONLY in the UI layer, not in the API
      for (const mlflowAssessment of latestAssessments.values()) {
        const assessment: Assessment = {
          assessment_id: mlflowAssessment.assessment_id,
          name: mlflowAssessment.name,
          value: mlflowAssessment.feedback?.value ?? mlflowAssessment.expectation?.value,
          type: mlflowAssessment.feedback ? "feedback" : "expectation",
          rationale: mlflowAssessment.metadata?.rationale, // Rationale is in metadata for both
          metadata: mlflowAssessment.metadata,
          source: mlflowAssessment.source,
          timestamp: mlflowAssessment.create_time_ms?.toString(),
        };
        assessmentMap.set(assessment.name, assessment);
      }
    }

    // Always set assessments, even if empty, to clear any previous values
    // This clears both remote assessments AND local changes when trace changes
    setAssessments(assessmentMap);
    // Reset auto-completed flag and pending update when trace changes
    setHasAutoCompleted(false);
    pendingUpdateRef.current = null;
  }, [trace, currentUser, currentTraceId]);

  // Reset auto-completed flag when item changes
  useEffect(() => {
    setHasAutoCompleted(false);
    pendingUpdateRef.current = null;
  }, [currentItem?.item_id]);

  // Check if all required assessments are complete and auto-update state
  useEffect(() => {
    // Only check if we have a current item and session schemas
    if (!currentItem || !session?.labeling_schemas || !allSchemas || hasAutoCompleted) {
      return;
    }

    // Don't auto-complete if the item is already completed or skipped
    if (currentItem.state === "COMPLETED" || currentItem.state === "SKIPPED") {
      return;
    }

    // Get all schemas for this session
    const sessionSchemas = session.labeling_schemas
      .map((ref) => allSchemas.find((schema) => schema.name === ref.name))
      .filter(Boolean) as LabelingSchema[];

    // Check if all schemas have assessments with values
    const allAssessmentsComplete = sessionSchemas.every((schema) => {
      const assessment = assessments.get(schema.name);
      const value = assessment?.value;

      // Check if assessment has a meaningful value
      if (value === undefined || value === null || value === "") {
        return false;
      }
      // For arrays, check if they have length
      if (Array.isArray(value) && value.length === 0) {
        return false;
      }
      // For objects (but not arrays), check if they have meaningful content
      if (typeof value === "object" && !Array.isArray(value) && Object.keys(value).length === 0) {
        return false;
      }
      return true;
    });

    // If all assessments are complete, update the item state to COMPLETED
    if (allAssessmentsComplete && sessionSchemas.length > 0) {
      // Check if we're already updating this item
      if (pendingUpdateRef.current === currentItem.item_id) {
        return;
      }


      // Set flags to prevent multiple updates
      setHasAutoCompleted(true);
      pendingUpdateRef.current = currentItem.item_id;

      // Update the item state to COMPLETED
      handleUpdateItem(currentItem.item_id, { state: "COMPLETED" })
        .then(() => {
          // Clear the pending update ref
          pendingUpdateRef.current = null;
          // Update the local items array to reflect the new state
          const updatedItems = [...items];
          updatedItems[currentItemIndex] = { ...currentItem, state: "COMPLETED" };
          // Note: We don't have setItems here, so the state will be updated on next fetch
        })
        .catch(() => {
          // Clear the pending update ref and reset the flag on error so it can be retried
          pendingUpdateRef.current = null;
          setHasAutoCompleted(false);
        });
    }
  }, [
    assessments,
    currentItem,
    session?.labeling_schemas,
    allSchemas,
    hasAutoCompleted,
    handleUpdateItem,
    currentItemIndex,
    items,
  ]);

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

  // Initial loading states - waiting for prerequisites
  if (isLoadingManifest || !session?.mlflow_run_id || isLoadingItems) {
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

  if (!currentItem || !reviewApp) {
    return <LoadingState />;
  }

  // Wait for traces to at least attempt loading (prevents flash)
  if (!hasAttemptedTraceLoad) {
    return <LoadingState />;
  }

  // If traces have been fetched but no matching trace found, show error
  if (!trace && !isLoadingTraces) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Trace Not Found</CardTitle>
            <CardDescription>
              Could not find trace {currentTraceId} in the session's traces. This trace may have
              been removed or is not linked to this session.
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

  // If we still don't have a trace at this point, show loading
  // This handles the case where traces are still loading
  if (!trace) {
    return <LoadingState />;
  }

  // Convert trace data to the expected format
  const traceData: Trace = {
    info: {
      trace_id: trace.info.trace_id,
      request_time: trace.info.request_time,
      execution_duration: trace.info.execution_duration,
      execution_duration_ms: trace.info.execution_duration_ms,
      state: trace.info.state,
      assessments: trace.info.assessments,
    },
    spans: trace.data?.spans || [],
  };

  // Compute schema assessments from session schemas and FILTERED assessments
  const schemaAssessments: SchemaAssessments | undefined =
    session?.labeling_schemas && allSchemas
      ? (() => {
          // Map session schema references to full schema objects
          const sessionSchemas = session.labeling_schemas
            .map((ref) => allSchemas.find((schema) => schema.name === ref.name))
            .filter(Boolean) as any[];

          // Use filtered assessments (only current user's assessments) instead of all assessments
          const filteredAssessmentsArray = Array.from(assessments.values());
          const combinedSchemas = combineSchemaWithAssessments(
            sessionSchemas,
            filteredAssessmentsArray
          );

          return {
            feedback: filterByType(combinedSchemas, "FEEDBACK"),
            expectations: filterByType(combinedSchemas, "EXPECTATION"),
          };
        })()
      : undefined;

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
            onUpdateItem={handleUpdateItem}
            onNavigateToIndex={handleNavigateToIndex}
            isLoading={isLoadingTraces}
            isSubmitting={updateItemMutation.isPending}
            schemaAssessments={schemaAssessments}
          />
        </div>
      </div>
    </div>
  );
}
