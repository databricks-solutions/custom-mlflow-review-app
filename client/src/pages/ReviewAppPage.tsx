import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { SMELabelingInterface } from "@/components/SMELabelingInterface";
import { NoSessionSelected } from "@/components/NoSessionSelected";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export function ReviewAppPage() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const traceId = searchParams.get("trace");

  if (!sessionId) {
    return <NoSessionSelected />;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header with back button */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-3xl font-bold">Review Session</h1>
      </div>

      {/* Divider */}
      <div className="border-t border-border"></div>

      {/* SME Interface */}
      <SMELabelingInterface
        sessionId={sessionId!}
        initialTraceId={traceId || undefined}
        hideNavigation={true}
      />
    </div>
  );
}
