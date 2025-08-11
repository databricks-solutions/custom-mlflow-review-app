import { useState, useEffect } from "react";
import { Markdown } from "@/components/ui/markdown";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  BarChart3,
  Brain,
  FileText,
  Play,
  RefreshCw,
  AlertTriangle,
  Info,
  ExternalLink,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";
import {
  useSessionAnalysis,
  useAnalysisStatus,
  useTriggerSessionAnalysis,
} from "@/hooks/api-hooks";
import { toast } from "sonner";

interface LabelingSessionAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewAppId: string;
  sessionId: string;
  sessionName: string;
  workspaceUrl?: string;
  mlflowRunId?: string;
}

// Interfaces for type checking - not exported
/* interface _AnalysisData {
  has_analysis: boolean;
  content?: string;
  session_id: string;
  run_id?: string;
  metadata?: {
    total_items_analyzed?: number;
    completed_assessments?: number;
    discovery_method?: string;
    analysis_timestamp?: string;
  };
  message?: string;
} */

/* interface _AnalysisStatus {
  session_id: string;
  status: "pending" | "running" | "completed" | "failed" | "not_found";
  message?: string;
  run_id?: string;
  report_path?: string;
} */

export function LabelingSessionAnalysisModal({
  isOpen,
  onClose,
  reviewAppId,
  sessionId,
  sessionName,
  workspaceUrl,
  mlflowRunId,
}: LabelingSessionAnalysisModalProps) {
  const [isPolling, setIsPolling] = useState(false);

  // Use the new API hooks
  const {
    data: analysisData,
    isLoading: isLoadingAnalysis,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useSessionAnalysis(reviewAppId, sessionId, isOpen);

  const { data: statusData, refetch: refetchStatus } = useAnalysisStatus(
    reviewAppId,
    sessionId,
    isOpen && isPolling
  );

  const triggerAnalysisMutation = useTriggerSessionAnalysis();

  // Smart polling management
  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;

    if (isPolling) {
      // Check if analysis is completed via status API
      if (statusData?.status === "completed") {
        setIsPolling(false);
        refetchAnalysis();
        toast.success("Analysis completed successfully!");
      }
      // Check if analysis failed
      else if (statusData?.status === "failed") {
        setIsPolling(false);
        toast.error(`Analysis failed: ${statusData.message}`);
      }
      // Fallback: If analysis data is available but status isn't "completed", stop polling
      else if (analysisData?.has_analysis && !isLoadingAnalysis) {
        console.log("Analysis data available, stopping polling as fallback");
        setIsPolling(false);
        toast.success("Analysis completed successfully!");
      }
      // Continue polling if still running/pending
      else if (statusData && (statusData.status === "running" || statusData.status === "pending")) {
        pollInterval = setTimeout(() => {
          refetchStatus();
        }, 2000);
      }
      // Stop polling if no status data after reasonable time (prevent infinite polling)
      else if (!statusData) {
        pollInterval = setTimeout(() => {
          refetchStatus();
        }, 2000);
      }
    }

    return () => {
      if (pollInterval) {
        clearTimeout(pollInterval);
      }
    };
  }, [isPolling, statusData, analysisData, isLoadingAnalysis, refetchAnalysis, refetchStatus]);

  // Check if there's already a running analysis when modal opens
  useEffect(() => {
    if (
      isOpen &&
      statusData &&
      (statusData.status === "running" || statusData.status === "pending")
    ) {
      setIsPolling(true);
    }
  }, [isOpen, statusData]);

  const handleTriggerAnalysis = () => {
    triggerAnalysisMutation.mutate(
      {
        reviewAppId,
        sessionId,
        includeAiInsights: true,
        modelEndpoint: "databricks-claude-sonnet-4",
      },
      {
        onSuccess: () => {
          setIsPolling(true);
          // Immediately refetch status to start polling cycle
          refetchStatus();
          toast.success("Analysis started! This may take a few minutes...");
        },
        onError: (error: Error) => {
          toast.error(`Failed to trigger analysis: ${error.message}`);
        },
      }
    );
  };

  const isRunning =
    statusData?.status === "running" ||
    statusData?.status === "pending" ||
    triggerAnalysisMutation.isPending;

  // Status icon helper
  const getStatusIcon = () => {
    if (isRunning) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    } else if (statusData?.status === "completed" || analysisData?.has_analysis) {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    } else if (statusData?.status === "failed") {
      return <XCircle className="h-4 w-4 text-red-600" />;
    }
    return null;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] flex flex-col" hideCloseButton>
        <DialogHeader className="space-y-4 pb-4">
          {/* Title row */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <DialogTitle className="flex items-center gap-2 text-xl">
                <BarChart3 className="h-5 w-5 shrink-0" />
                Session Analysis
                {getStatusIcon()}
              </DialogTitle>
              <DialogDescription className="mt-1">
                Analysis for "{sessionName}"
                {statusData?.status && statusData.status !== "not_found" && (
                  <Badge variant="outline" className="ml-2">
                    {statusData.status.replace("_", " ")}
                  </Badge>
                )}
              </DialogDescription>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 shrink-0">
              {workspaceUrl && mlflowRunId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    window.open(`${workspaceUrl}/ml/experiments/runs/${mlflowRunId}`, "_blank");
                  }}
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  MLflow Run
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={handleTriggerAnalysis}
                disabled={isRunning}
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                    Computing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    {analysisData?.has_analysis ? "Re-run Analysis" : "Run Analysis"}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto min-h-0 relative">
          {/* Loading overlay when analysis is running */}
          {isRunning && analysisData?.has_analysis && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-10 flex items-center justify-center">
              <div className="bg-card p-6 rounded-lg shadow-lg border flex flex-col items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <div className="text-center">
                  <p className="font-medium">Analyzing Session</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {statusData?.message || "This may take a few minutes..."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {isLoadingAnalysis ? (
            <div className="space-y-4 p-4">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : analysisError ? (
            <Alert className="m-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Failed to load analysis: {(analysisError as Error)?.message || "Unknown error"}
              </AlertDescription>
            </Alert>
          ) : !analysisData?.has_analysis ? (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center">
              <Brain className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No Analysis Available</h3>
              <p className="text-muted-foreground mb-6 max-w-md">
                {analysisData?.message ||
                  "Generate insights from SME assessments by running an analysis. This will analyze labeling patterns, identify critical issues, and provide actionable recommendations."}
              </p>
              <Button onClick={handleTriggerAnalysis} disabled={isRunning}>
                {isRunning ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Computing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Analysis
                  </>
                )}
              </Button>

              {isRunning && statusData?.message && (
                <Alert className="mt-4 max-w-md">
                  <Info className="h-4 w-4" />
                  <AlertDescription>{statusData.message}</AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <div className="px-6 py-4">
              {/* Analysis metadata header - simplified */}
              {analysisData?.metadata && (
                <div className="flex items-center gap-4 text-sm text-muted-foreground pb-4 mb-4 border-b">
                  {analysisData.metadata.completed_assessments !== undefined && (
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      <span>
                        {analysisData.metadata.completed_assessments} labeled traces analyzed
                      </span>
                    </div>
                  )}
                  {analysisData.metadata.total_traces_analyzed && (
                    <div className="flex items-center gap-1">
                      <BarChart3 className="h-4 w-4" />
                      <span>
                        {analysisData.metadata.total_traces_analyzed} total traces in session
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Analysis report content */}
              <Markdown
                content={analysisData.content}
                variant="default"
                className="text-foreground"
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
