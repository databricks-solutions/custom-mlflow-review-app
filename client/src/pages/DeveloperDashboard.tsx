import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TraceExplorer } from "@/components/TraceExplorer";
import { LabelingSchemasPage } from "./LabelingSchemasPage";
import { LabelingSessionsTab } from "@/components/LabelingSessionsTab";
import { ExperimentAnalysis } from "@/components/ExperimentAnalysis";
import {
  ArrowLeft,
  Users,
  Tag,
  BookOpen,
  ExternalLink,
  Settings,
} from "lucide-react";
import {
  useAppManifest,
} from "@/hooks/api-hooks";

export function DeveloperDashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Get tab from URL params, default to sessions
  const initialTab = searchParams.get("tab") || "sessions";
  const [activeTab, setActiveTab] = useState(initialTab);

  // Function to update tab and URL
  const handleTabChange = (newTab: string) => {
    setActiveTab(newTab);
    const newSearchParams = new URLSearchParams(searchParams);
    newSearchParams.set("tab", newTab);
    setSearchParams(newSearchParams);
  };

  // Get app manifest (contains config, user, workspace, and review app)
  const { data: manifest, isLoading: isLoadingManifest } = useAppManifest();
  const EXPERIMENT_ID = manifest?.config?.experiment_id;
  const currentUser = manifest?.user;
  const workspaceData = manifest?.workspace ? { workspace: manifest.workspace } : null;

  // Get review app info from manifest instead of separate API call
  const reviewApp = manifest?.review_app;

  if (isLoadingManifest) {
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
              No review app found for this experiment. Create one to start labeling traces.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="p-0 h-auto text-2xl font-bold text-foreground hover:text-foreground"
                    onClick={() => navigate('/dev')}
                  >
                    Developer Dashboard
                  </Button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Info section */}
          <div className="text-right space-y-2">
              {EXPERIMENT_ID && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">Experiment:</span>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      {workspaceData?.workspace?.url ? (
                        <a
                          href={`${workspaceData.workspace.url}/ml/experiments/${EXPERIMENT_ID}/traces`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                        >
                          {EXPERIMENT_ID}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="font-mono text-sm cursor-help">{EXPERIMENT_ID}</span>
                      )}
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="max-w-xs">
                        <p className="font-semibold">
                          {manifest?.config?.experiment_name || "Loading..."}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Experiment ID: {EXPERIMENT_ID}
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            )}
            {reviewApp?.review_app_id && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">Review App:</span>
                {workspaceData?.workspace?.url ? (
                  <a
                    href={`${workspaceData.workspace.url}/ml/review-v2/${reviewApp.review_app_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                  >
                    {reviewApp.review_app_id.slice(0, 8)}...
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ) : (
                  <span className="font-mono text-sm">
                    {reviewApp.review_app_id.slice(0, 8)}...
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
          <TabsList>
            <TabsTrigger value="sessions" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Labeling Sessions
            </TabsTrigger>
            <TabsTrigger value="schemas" className="flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Label Schemas
            </TabsTrigger>
            <TabsTrigger value="summary" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Analysis Summary
            </TabsTrigger>
          </TabsList>

          {/* Labeling Sessions Tab */}
          <TabsContent value="sessions" className="space-y-4">
            <LabelingSessionsTab
              reviewApp={reviewApp}
              currentUser={currentUser}
              workspaceData={workspaceData}
              experimentId={EXPERIMENT_ID || ""}
            />
          </TabsContent>

          {/* Label Schemas Tab */}
          <TabsContent value="schemas" className="space-y-4">
            <LabelingSchemasPage />
          </TabsContent>

          {/* Experiment Summary Tab */}
          <TabsContent value="summary" className="space-y-4">
            <ExperimentAnalysis
              experimentId={EXPERIMENT_ID || ""}
            />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}