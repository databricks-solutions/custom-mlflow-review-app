import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ChevronRight, Wrench } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  useCurrentUser,
  useLabelingSessions,
  useLabelingItems,
  useUserRole,
  useAppManifest,
} from "@/hooks/api-hooks";

// Helper component to show progress for each labeling session
function SessionProgress({ reviewAppId, sessionId }: { reviewAppId: string; sessionId: string }) {
  // Get items for this specific session
  const { data: itemsData, isLoading } = useLabelingItems(
    reviewAppId,
    sessionId,
    !!reviewAppId && !!sessionId
  );

  if (isLoading) {
    return (
      <div className="flex items-center gap-4">
        <span className="text-sm">Your progress: </span>
        <div className="animate-pulse h-2 bg-gray-200 rounded w-24"></div>
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  const items = itemsData?.items || [];

  if (items.length === 0) {
    return <div className="text-sm text-muted-foreground">No chats to review.</div>;
  }

  const completedCount = items.filter((i) => i.state === "COMPLETED").length;
  const progressPercentage = Math.round((completedCount / items.length) * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-4">
        <span className="text-sm">Your progress: </span>
        <span className="text-sm font-semibold">{progressPercentage}%</span>
      </div>
      <div className="flex items-center gap-3">
        <Progress value={progressPercentage} className="h-2 flex-1" />
        <span className="text-sm text-muted-foreground">
          {completedCount}/{items.length}
        </span>
      </div>
    </div>
  );
}

export function LabelingPage() {
  const navigate = useNavigate();

  // Get app manifest (contains review app info)
  const { data: manifest } = useAppManifest();
  const reviewApp = manifest?.review_app;

  // Get current user info
  const { data: userInfo } = useCurrentUser();

  // Get user role to determine if dev button should be shown
  const { data: userRole } = useUserRole();

  // Get labeling sessions (server determines review app based on config)
  const { data: sessionsData, isLoading: isLoadingSessions } = useLabelingSessions();

  // Filter sessions assigned to current user
  const userSessions = sessionsData?.labeling_sessions?.filter((session) =>
    session.assigned_users?.includes(userInfo?.userName || "")
  );

  // Get user's first name for greeting
  const firstName =
    userInfo?.displayName?.split(" ")[0] || userInfo?.userName?.split("@")[0] || "there";

  if (isLoadingSessions) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  if (!reviewApp) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>No Review App Found</CardTitle>
            <CardDescription>
              No review app has been configured for this experiment. Please contact your
              administrator.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Welcome Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-light">Hi, {firstName}</h2>
          <div className="flex items-center gap-4">
            {userRole?.is_developer && (
              <Button variant="outline" onClick={() => navigate("/dev")}>
                <Wrench className="h-4 w-4 mr-2" />
                Developer Dashboard
              </Button>
            )}
          </div>
        </div>

        <p className="text-muted-foreground max-w-4xl">
          Thank you for participating to improve the quality of this Agent. Your expertise has made
          a huge impact, and every interaction you've reviewed helps the chatbot become smarter and
          more user-friendly. Thank you for your dedication and valuable insights.
        </p>
      </div>

      {/* Labeling Sessions Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Chats to review</CardTitle>
          <CardDescription>
            For each chat, review the conversation thread. Then answer the questions while reviewing
            the chat content and data sourced for the response.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!userSessions || userSessions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                You don't have any labeling sessions assigned. Contact your team lead to get
                assigned to a session.
              </p>
            </div>
          ) : (
            userSessions.map((session) => (
              <div key={session.labeling_session_id} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold">{session.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {new Date(session.create_time || "").toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>

                <SessionProgress
                  reviewAppId={reviewApp.review_app_id || ""}
                  sessionId={session.labeling_session_id || ""}
                />

                <div className="flex justify-end">
                  <Button
                    onClick={() => navigate(`/review/${session.labeling_session_id}`)}
                    className="flex items-center gap-2"
                  >
                    Start review
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                {/* Divider */}
                <div className="border-t" />
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
