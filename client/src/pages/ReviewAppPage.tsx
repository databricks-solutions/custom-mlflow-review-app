import { useParams, useSearchParams } from "react-router-dom";
import { SMELabelingInterface } from "@/components/SMELabelingInterface";
import { NoSessionSelected } from "@/components/NoSessionSelected";

export function ReviewAppPage() {
  const { reviewAppId, sessionId: urlSessionId } = useParams<{ 
    reviewAppId?: string; 
    sessionId?: string; 
  }>();
  const [searchParams] = useSearchParams();

  // Support both URL structures:
  // New: /review/:sessionId  
  // Old: /review-app/:reviewAppId?session=:sessionId
  const sessionId = urlSessionId || searchParams.get("session");

  if (!sessionId) {
    return <NoSessionSelected />;
  }

  // For the new URL structure, we don't need reviewAppId since we can get it from the session
  // For the old URL structure, we pass the reviewAppId
  return <SMELabelingInterface 
    reviewAppId={reviewAppId || undefined} 
    sessionId={sessionId!} 
  />;
}
