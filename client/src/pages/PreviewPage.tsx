import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SMELabelingInterface } from "@/components/SMELabelingInterface";
import { RendererSelector } from "@/components/RendererSelector";
import { LoadingState } from "@/components/LoadingState";
import { NoSessionSelected } from "@/components/NoSessionSelected";
import { useAppManifest, useLabelingSession } from "@/hooks/api-hooks";

export function PreviewPage() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();

  // Get the current review app from manifest
  const { data: manifest, isLoading: isLoadingManifest } = useAppManifest();
  const reviewApp = manifest?.review_app;

  // Get session data
  const { data: session } = useLabelingSession(
    sessionId || "",
    !!sessionId
  );

  if (!sessionId) {
    return <NoSessionSelected />;
  }

  // Wait for review app to load before showing preview
  if (isLoadingManifest || !reviewApp) {
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
            <RendererSelector runId={session.mlflow_run_id} sessionName={session.name} />
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-border"></div>

      {/* Direct SME UI without card wrapper */}
      <SMELabelingInterface sessionId={sessionId!} hideNavigation={true} />
    </div>
  );
}
