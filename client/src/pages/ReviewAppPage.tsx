import { useParams, useSearchParams } from "react-router-dom";
import { SMELabelingInterface } from "@/components/SMELabelingInterface";
import { NoSessionSelected } from "@/components/NoSessionSelected";

export function ReviewAppPage() {
  const { reviewAppId } = useParams<{ reviewAppId: string }>();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get("session");

  if (!sessionId) {
    return <NoSessionSelected />;
  }

  return <SMELabelingInterface reviewAppId={reviewAppId!} sessionId={sessionId!} />;
}
