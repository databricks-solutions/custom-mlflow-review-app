import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SMELabelingInterface } from "@/components/SMELabelingInterface";
import { RendererSelector } from "@/components/RendererSelector";
import { LoadingState } from "@/components/LoadingState";
import { NoSessionSelected } from "@/components/NoSessionSelected";
import {
  useCurrentReviewApp,
  useLabelingSession,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";

export function PreviewPage() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();

  // Get the current review app (implicitly determined by server config)
  const { data: reviewApp, isLoading: isLoadingReviewApp } = useCurrentReviewApp();
  
  // Get session data
  const { data: session } = useLabelingSession(
    reviewApp?.review_app_id || "", 
    sessionId || "", 
    !!reviewApp?.review_app_id && !!sessionId
  );

  if (!sessionId) {
    return <NoSessionSelected />;
  }

  // Wait for review app to load before showing preview
  if (isLoadingReviewApp || !reviewApp) {
    return <LoadingState />;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Button variant="ghost" size="sm" onClick={() => navigate("/dev")}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-3xl font-bold">Session Preview</h1>
          </div>
        </div>
        
        {/* Compact Renderer Selector on the same line */}
        <div className="ml-6">
          {session?.mlflow_run_id && (
            <RendererSelector 
              runId={session.mlflow_run_id} 
              sessionName={session.name}
            />
          )}
        </div>
      </div>
      
      {/* Divider */}
      <div className="border-t border-border"></div>
      
      {/* Direct SME UI without card wrapper */}
      <SMELabelingInterface 
        sessionId={sessionId!} 
        hideNavigation={true} 
      />
    </div>
  );
}