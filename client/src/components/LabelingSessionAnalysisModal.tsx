import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  BarChart3,
  Brain,
  Clock,
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
import { useSessionAnalysis, useAnalysisStatus, useTriggerSessionAnalysis } from "@/hooks/api-hooks";
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

interface AnalysisData {
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
}

interface AnalysisStatus {
  session_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'not_found';
  message?: string;
  run_id?: string;
  report_path?: string;
}

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

  const {
    data: statusData,
    refetch: refetchStatus,
  } = useAnalysisStatus(reviewAppId, sessionId, isOpen && isPolling);

  const triggerAnalysisMutation = useTriggerSessionAnalysis();

  // Smart polling management
  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    
    if (isPolling && statusData) {
      if (statusData.status === 'completed') {
        setIsPolling(false);
        refetchAnalysis();
        toast.success('Analysis completed successfully!');
      } else if (statusData.status === 'failed') {
        setIsPolling(false);
        toast.error(`Analysis failed: ${statusData.message}`);
      } else if (statusData.status === 'running' || statusData.status === 'pending') {
        // Continue polling
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
  }, [isPolling, statusData, refetchAnalysis, refetchStatus]);

  // Check if there's already a running analysis when modal opens
  useEffect(() => {
    if (isOpen && statusData && (statusData.status === 'running' || statusData.status === 'pending')) {
      setIsPolling(true);
    }
  }, [isOpen, statusData]);

  const handleTriggerAnalysis = () => {
    triggerAnalysisMutation.mutate({
      reviewAppId,
      sessionId,
      includeAiInsights: true,
      modelEndpoint: 'databricks-claude-sonnet-4',
    }, {
      onSuccess: () => {
        setIsPolling(true);
        toast.success('Analysis started! This may take a few minutes...');
      },
      onError: (error: any) => {
        toast.error(`Failed to trigger analysis: ${error.message}`);
      },
    });
  };

  const isRunning = statusData?.status === 'running' || statusData?.status === 'pending' || triggerAnalysisMutation.isPending;

  // Status icon helper
  const getStatusIcon = () => {
    if (statusData?.status === 'running' || triggerAnalysisMutation.isPending) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    } else if (statusData?.status === 'completed') {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    } else if (statusData?.status === 'failed') {
      return <XCircle className="h-4 w-4 text-red-600" />;
    }
    return null;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Session Analysis
                {getStatusIcon()}
              </DialogTitle>
              <DialogDescription>
                Analysis for "{sessionName}"
                {statusData?.status && statusData.status !== 'not_found' && (
                  <Badge variant="outline" className="ml-2">
                    {statusData.status.replace('_', ' ')}
                  </Badge>
                )}
              </DialogDescription>
            </div>
            
            {/* Action buttons */}
            <div className="flex items-center gap-2">
              {workspaceUrl && mlflowRunId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    window.open(
                      `${workspaceUrl}/ml/experiments/runs/${mlflowRunId}`,
                      '_blank'
                    );
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
                    {statusData?.status === 'running' ? 'Analyzing...' : 'Starting...'}
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    {analysisData?.has_analysis ? 'Re-run Analysis' : 'Run Analysis'}
                  </>
                )}
              </Button>
            </div>
          </div>
          
          {/* Status indicators */}
          {analysisData?.metadata && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                {analysisData.metadata.completed_assessments || 0} assessments analyzed
              </div>
              {analysisData.metadata.analysis_timestamp && (
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {new Date(analysisData.metadata.analysis_timestamp).toLocaleString()}
                </div>
              )}
              {analysisData.metadata.discovery_method && (
                <Badge variant="outline" className="text-xs">
                  {analysisData.metadata.discovery_method}
                </Badge>
              )}
            </div>
          )}
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
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
                Failed to load analysis: {(analysisError as any)?.message || 'Unknown error'}
              </AlertDescription>
            </Alert>
          ) : !analysisData?.has_analysis ? (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center">
              <Brain className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No Analysis Available</h3>
              <p className="text-muted-foreground mb-6 max-w-md">
                {analysisData?.message || 
                 'Generate insights from SME assessments by running an analysis. This will analyze labeling patterns, identify critical issues, and provide actionable recommendations.'}
              </p>
              <Button onClick={handleTriggerAnalysis} disabled={isRunning}>
                {isRunning ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analysis Starting...
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
                  <AlertDescription>
                    {statusData.message}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <ScrollArea className="h-full">
              <div className="p-6">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  className="prose prose-sm max-w-none dark:prose-invert
                    prose-headings:scroll-m-20 prose-headings:tracking-tight
                    prose-h1:text-2xl prose-h1:font-bold
                    prose-h2:text-xl prose-h2:font-semibold prose-h2:border-b prose-h2:pb-2
                    prose-h3:text-lg prose-h3:font-medium
                    prose-p:leading-7 prose-p:mb-4
                    prose-ul:my-4 prose-li:my-1
                    prose-blockquote:border-l-4 prose-blockquote:border-border prose-blockquote:pl-4 prose-blockquote:italic
                    prose-code:relative prose-code:rounded prose-code:bg-muted prose-code:px-[0.3rem] prose-code:py-[0.2rem] prose-code:font-mono prose-code:text-sm
                    prose-pre:overflow-x-auto prose-pre:rounded-lg prose-pre:border prose-pre:bg-muted prose-pre:p-4
                    prose-table:w-full prose-table:border-collapse prose-table:border prose-table:border-border
                    prose-th:border prose-th:border-border prose-th:bg-muted/50 prose-th:px-4 prose-th:py-2 prose-th:text-left prose-th:font-medium
                    prose-td:border prose-td:border-border prose-td:px-4 prose-td:py-2
                    prose-strong:font-semibold
                    prose-em:italic"
                >
                  {analysisData.content}
                </ReactMarkdown>
              </div>
            </ScrollArea>
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