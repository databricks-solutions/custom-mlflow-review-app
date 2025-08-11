import { useState, useMemo, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { LabelingSessionItemsTable } from "@/components/LabelingSessionItemsTable";
import { LabelingSessionAnalysisModal } from "@/components/LabelingSessionAnalysisModal";
import { TraceExplorer } from "@/components/TraceExplorer";
import {
  Plus,
  Info,
  ExternalLink,
  BarChart3,
  Eye,
  Trash2,
  Tag,
} from "lucide-react";
import { ReviewApp, LabelingSession } from "@/types/renderers";
import {
  useLabelingSessions,
  useCreateLabelingSession,
  useDeleteLabelingSession,
  useLabelingItems,
  useSearchTraces,
  useLabelSchemas,
  queryKeys,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

// Wrapper component to fetch items data for LabelingSessionItemsTable
function SessionItemsWrapper({
  reviewAppId,
  sessionId,
  reviewApp,
}: {
  reviewAppId: string;
  sessionId: string;
  reviewApp: ReviewApp | null | undefined;
}) {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Trace explorer modal state
  const [traceExplorerOpen, setTraceExplorerOpen] = useState(false);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  // Handle trace click to open modal
  const handleTraceClick = (traceId: string) => {
    setSelectedTraceId(traceId);
    setTraceExplorerOpen(true);
  };

  // Intersection Observer for lazy loading
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            // Once visible, we can stop observing
            observer.unobserve(entry.target);
          }
        });
      },
      {
        rootMargin: '100px', // Start loading 100px before the element comes into view
      }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  const { data: itemsData, isLoading } = useLabelingItems(
    reviewAppId,
    sessionId,
    isVisible && !!reviewAppId && !!sessionId
  );

  return (
    <div ref={containerRef}>
      {!isVisible ? (
        <div className="border rounded-lg p-4 text-center text-muted-foreground">
          Loading session items...
        </div>
      ) : isLoading ? (
        <div className="border rounded-lg overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="h-10 px-2 text-left align-middle font-medium">
                  <Skeleton className="h-4 w-12" />
                </th>
                <th className="h-10 px-2 text-left align-middle font-medium">
                  <Skeleton className="h-4 w-16" />
                </th>
                <th className="h-10 px-2 text-left align-middle font-medium">
                  <Skeleton className="h-4 w-20" />
                </th>
                <th className="h-10 px-2 text-left align-middle font-medium">
                  <Skeleton className="h-4 w-24" />
                </th>
                <th className="h-10 px-2 text-left align-middle font-medium">
                  <Skeleton className="h-4 w-16" />
                </th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b">
                  <td className="p-2">
                    <Skeleton className="h-6 w-16 rounded" />
                  </td>
                  <td className="p-2">
                    <Skeleton className="h-4 w-32" />
                  </td>
                  <td className="p-2">
                    <Skeleton className="h-4 w-40" />
                  </td>
                  <td className="p-2">
                    <Skeleton className="h-4 w-20" />
                  </td>
                  <td className="p-2">
                    <Skeleton className="h-4 w-24" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <LabelingSessionItemsTable
          items={itemsData?.items || []}
          reviewApp={reviewApp}
          reviewAppId={reviewAppId}
          sessionId={sessionId}
          onTraceClick={handleTraceClick}
        />
      )}
      
      {/* Trace Explorer Modal */}
      <Dialog open={traceExplorerOpen} onOpenChange={setTraceExplorerOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>Trace Explorer</DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto max-h-[80vh]">
            {selectedTraceId && (
              <TraceExplorer traceId={selectedTraceId} />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface LabelingSessionsTabProps {
  reviewApp: ReviewApp;
  currentUser: any;
  workspaceData: any;
  experimentId: string;
}

export function LabelingSessionsTab({
  reviewApp,
  currentUser,
  workspaceData,
  experimentId,
}: LabelingSessionsTabProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();

  // Session creation state
  const [isCreateSessionOpen, setIsCreateSessionOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState("");
  const [assignedUsers, setAssignedUsers] = useState("");
  const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());

  // Analysis modal state
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [selectedAnalysisSession, setSelectedAnalysisSession] = useState<LabelingSession | null>(
    null
  );

  // Get highlighted session ID from URL params
  const highlightSessionId = searchParams.get("highlight");

  // Fetch labeling sessions - only when this component is rendered
  const { data: sessionsData, isLoading: isLoadingSessions } = useLabelingSessions(
    !!reviewApp?.review_app_id
  );

  // Fetch available label schemas
  const { data: labelSchemas, isLoading: isLoadingSchemas } = useLabelSchemas();

  // Create labeling session mutation
  const createSessionMutation = useCreateLabelingSession();
  
  // Delete labeling session mutation
  const deleteSessionMutation = useDeleteLabelingSession();

  // Delete confirmation state
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<string | null>(null);

  const handleCreateSession = () => {
    if (!newSessionName || !reviewApp?.review_app_id) return;

    // Require at least one schema to be selected
    if (selectedSchemas.size === 0) {
      toast.error("Please select at least one labeling schema");
      return;
    }

    // Auto-add current user if not already included
    let userEmails = assignedUsers ? assignedUsers.split(",").map((email) => email.trim()) : [];
    if (currentUser?.email && !userEmails.includes(currentUser.email)) {
      userEmails.push(currentUser.email);
    }

    // Convert selected schema names to the required format
    const selectedSchemaObjects = Array.from(selectedSchemas).map((name) => ({ name }));

    createSessionMutation.mutate(
      {
        reviewAppId: reviewApp.review_app_id,
        session: {
          name: newSessionName,
          assigned_users: userEmails,
          labeling_schemas: selectedSchemaObjects,
        },
      },
      {
        onSuccess: () => {
          setIsCreateSessionOpen(false);
          setNewSessionName("");
          setAssignedUsers("");
          setSelectedSchemas(new Set());
          toast.success("Labeling session created successfully");
        },
      }
    );
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSessionMutation.mutateAsync({ sessionId });
      setDeleteConfirmDialog(null);
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  if (isLoadingSessions) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Labeling Sessions</h2>
        <Dialog
          open={isCreateSessionOpen}
          onOpenChange={(open) => {
            setIsCreateSessionOpen(open);
            // Reset selected schemas when dialog opens
            if (open) {
              setSelectedSchemas(new Set());
            }
          }}
        >
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Session
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Labeling Session</DialogTitle>
              <DialogDescription>
                Create a new session for reviewers to label traces.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Session Name</Label>
                <Input
                  id="name"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  placeholder="e.g., Week 1 Review"
                />
              </div>
              <div className="grid gap-2">
                <Label>Labeling Schemas</Label>
                <p className="text-sm text-muted-foreground mb-2">
                  Select which evaluation criteria to include in this session
                </p>
                {labelSchemas && labelSchemas.length > 0 ? (
                  <div className="border rounded-lg p-4 max-h-60 overflow-y-auto space-y-3">
                    {[...labelSchemas]
                      .sort((a, b) => (a.title || a.name).localeCompare(b.title || b.name))
                      .map((schema) => (
                        <div key={schema.name} className="flex items-start space-x-3">
                          <Checkbox
                            id={`schema-${schema.name}`}
                            checked={selectedSchemas.has(schema.name)}
                            onCheckedChange={(checked) => {
                              const newSelected = new Set(selectedSchemas);
                              if (checked) {
                                newSelected.add(schema.name);
                              } else {
                                newSelected.delete(schema.name);
                              }
                              setSelectedSchemas(newSelected);
                            }}
                          />
                          <div className="grid gap-1.5 leading-none flex-1">
                            <label
                              htmlFor={`schema-${schema.name}`}
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                            >
                              {schema.title || schema.name}
                            </label>
                            {schema.description && (
                              <p className="text-xs text-muted-foreground">
                                {schema.description}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No labeling schemas found. Create schemas first to enable structured evaluation.
                  </p>
                )}
                {selectedSchemas.size > 0 && (
                  <p className="text-sm text-muted-foreground">
                    {selectedSchemas.size} schema{selectedSchemas.size !== 1 ? "s" : ""}{" "}
                    selected
                  </p>
                )}
              </div>
              <div className="grid gap-2">
                <Label htmlFor="users">Assigned Users (comma-separated emails)</Label>
                <Textarea
                  id="users"
                  value={assignedUsers}
                  onChange={(e) => setAssignedUsers(e.target.value)}
                  placeholder="user1@example.com, user2@example.com"
                  rows={2}
                />
                <p className="text-xs text-muted-foreground">
                  Current user ({currentUser?.email}) will be automatically added
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreateSession}
                disabled={
                  !newSessionName ||
                  selectedSchemas.size === 0 ||
                  createSessionMutation.isPending
                }
              >
                {createSessionMutation.isPending ? "Creating..." : "Create Session"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {sessionsData?.labeling_sessions && sessionsData.labeling_sessions.length > 0 ? (
        <div className="grid gap-4 overflow-x-hidden">
          {sessionsData.labeling_sessions
            .sort(
              (a, b) => new Date(b.create_time).getTime() - new Date(a.create_time).getTime()
            )
            .map((session) => {
              const isHighlighted = highlightSessionId === session.labeling_session_id;

              return (
                <Card
                  key={session.labeling_session_id}
                  className={isHighlighted ? "ring-2 ring-blue-500" : ""}
                >
                  <CardHeader className="pb-3">
                    {/* Title row with links and buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CardTitle className="text-lg">{session.name}</CardTitle>
                        {workspaceData?.workspace?.url && (
                          <>
                            <a
                              href={`${workspaceData.workspace.url}/ml/experiments/${experimentId}/labeling-sessions?selectedLabelingSessionId=${session.labeling_session_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                            >
                              session
                              <ExternalLink className="h-3 w-3" />
                            </a>
                            <a
                              href={`${workspaceData.workspace.url}/ml/experiments/${experimentId}/evaluation-runs?selectedRunUuid=${session.mlflow_run_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                            >
                              run
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/preview/${session.labeling_session_id}`)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Preview
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedAnalysisSession(session);
                            setAnalysisModalOpen(true);
                          }}
                        >
                          <BarChart3 className="h-4 w-4 mr-1" />
                          Analysis
                        </Button>
                        <AddTracesButton
                          reviewAppId={reviewApp?.review_app_id || ""}
                          sessionId={session.labeling_session_id}
                          session={session}
                          experimentId={experimentId || ""}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setDeleteConfirmDialog(session.labeling_session_id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    {/* Created date and by line */}
                    <CardDescription className="mt-2 space-y-2">
                      <div>Created {new Date(session.create_time).toLocaleDateString()} by {session.created_by}</div>
                      {session.assigned_users && session.assigned_users.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">assigned users</div>
                          <div className="flex flex-wrap gap-1">
                            {session.assigned_users.map((user, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {user}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-4">

                      {session.labeling_schemas && session.labeling_schemas.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Selected Schemas</div>
                          <div className="flex flex-wrap gap-2">
                            {session.labeling_schemas.map((schema, index) => (
                              <Button
                                key={index}
                                variant="outline"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => navigate(`/dev?tab=schemas`)}
                              >
                                <Tag className="h-3 w-3 mr-1" />
                                {schema.name}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}

                      <SessionItemsWrapper
                        reviewAppId={reviewApp?.review_app_id || ""}
                        sessionId={session.labeling_session_id}
                        reviewApp={reviewApp}
                      />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              No Labeling Sessions
            </CardTitle>
            <CardDescription>
              Create a labeling session to organize trace reviews and collect SME feedback.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <LabelingSessionAnalysisModal
        isOpen={analysisModalOpen}
        onClose={() => setAnalysisModalOpen(false)}
        session={selectedAnalysisSession}
        reviewAppId={reviewApp?.review_app_id || ""}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialog !== null} onOpenChange={() => setDeleteConfirmDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Labeling Session</DialogTitle>
            <DialogDescription>
              <div className="space-y-2">
                <p>
                  Are you sure you want to delete this labeling session? This action cannot be undone.
                </p>
                <p className="text-sm text-muted-foreground">
                  All labeling items and progress for this session will be permanently removed.
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmDialog && handleDeleteSession(deleteConfirmDialog)}
              disabled={deleteSessionMutation.isPending}
            >
              {deleteSessionMutation.isPending ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Delete Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// AddTracesButton component - this should be extracted from DeveloperDashboard
function AddTracesButton({
  reviewAppId,
  sessionId,
  session,
  experimentId,
}: {
  reviewAppId: string;
  sessionId: string;
  session: LabelingSession;
  experimentId: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedTraces, setSelectedTraces] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [allTraces, setAllTraces] = useState<Array<{ trace_id: string; [key: string]: unknown }>>(
    []
  );
  const queryClient = useQueryClient();

  // Get current items to check which traces are already in session
  const { data: itemsData } = useLabelingItems(
    reviewAppId,
    sessionId,
    isOpen && !!reviewAppId && !!sessionId
  );

  const existingTraceIds = useMemo(() => {
    return new Set((itemsData?.items || []).map((item) => item.source?.trace_id).filter(Boolean));
  }, [itemsData]);

  // Search traces
  const {
    data: tracesData,
    isLoading: isLoadingTraces,
    refetch: searchTraces,
  } = useSearchTraces(
    {
      experiment_ids: experimentId ? [experimentId] : [],
      filter: searchFilter || undefined,
      max_results: 50 * currentPage,
      include_spans: false,
    },
    !!experimentId && isOpen
  );

  // Update local traces state when data changes
  useEffect(() => {
    if (tracesData?.traces) {
      setAllTraces(tracesData.traces);
      setHasNextPage(tracesData.traces.length === 50 * currentPage);
    }
  }, [tracesData, currentPage]);

  // Link traces mutation
  const linkTracesMutation = useMutation({
    mutationFn: async (traceIds: string[]) => {
      if (!session?.mlflow_run_id) throw new Error("No MLflow run ID for session");
      const response = await apiClient.api.linkTracesToSession({
        reviewAppId,
        sessionId,
        mlflow_run_id: session.mlflow_run_id,
        trace_ids: traceIds,
      });
      return response;
    },
    onSuccess: (data, traceIds) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.labelingItems.list(reviewAppId, sessionId),
      });
      setSelectedTraces(new Set());
      searchTraces();
      toast.success(
        `Successfully linked ${traceIds.length} trace${traceIds.length !== 1 ? "s" : ""} to the session`
      );
    },
    onError: (error: Error) => {
      toast.error(`Failed to link traces: ${error.message}`);
    },
  });

  const handleLinkTraces = () => {
    if (selectedTraces.size > 0) {
      linkTracesMutation.mutate(Array.from(selectedTraces));
    }
  };

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchFilter("");
      setSelectedTraces(new Set());
      setCurrentPage(1);
      setAllTraces([]);
    }
  }, [isOpen]);

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <Plus className="h-4 w-4 mr-1" />
        Add Traces
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Add Traces to Session</DialogTitle>
            <DialogDescription>
              Search for traces and add them to "{session?.name || "this session"}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Enter filter (e.g., attributes.status = 'SUCCESS')"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchTraces()}
              />
              <Button onClick={() => searchTraces()}>Search</Button>
            </div>
            {selectedTraces.size > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {selectedTraces.size} trace{selectedTraces.size !== 1 ? "s" : ""} selected
                </span>
                <Button size="sm" onClick={handleLinkTraces} disabled={linkTracesMutation.isPending}>
                  {linkTracesMutation.isPending ? "Linking..." : "Link Selected"}
                </Button>
              </div>
            )}

            {/* Traces table */}
            <div className="border rounded-lg max-h-96 overflow-y-auto">
              {isLoadingTraces ? (
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr className="border-b">
                      <th className="text-left p-2 font-medium">
                        <Skeleton className="h-4 w-4" />
                      </th>
                      <th className="text-left p-2 font-medium">Trace ID</th>
                      <th className="text-left p-2 font-medium">Status</th>
                      <th className="text-left p-2 font-medium">Start Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from({ length: 8 }, (_, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-2">
                          <Skeleton className="h-4 w-4" />
                        </td>
                        <td className="p-2">
                          <Skeleton className="h-4 w-16" />
                        </td>
                        <td className="p-2">
                          <Skeleton className="h-5 w-12" />
                        </td>
                        <td className="p-2">
                          <Skeleton className="h-4 w-24" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : allTraces.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  {searchFilter ? "No traces found matching your search" : "Enter a search filter and click Search to find traces"}
                </div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-muted/50">
                    <tr className="border-b">
                      <th className="text-left p-2">
                        <Checkbox
                          checked={allTraces.length > 0 && selectedTraces.size === allTraces.filter(t => !existingTraceIds.has(t.trace_id)).length}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              const availableTraces = allTraces.filter(t => !existingTraceIds.has(t.trace_id));
                              setSelectedTraces(new Set(availableTraces.map(t => t.trace_id)));
                            } else {
                              setSelectedTraces(new Set());
                            }
                          }}
                        />
                      </th>
                      <th className="text-left p-2 font-medium">Trace ID</th>
                      <th className="text-left p-2 font-medium">Status</th>
                      <th className="text-left p-2 font-medium">Start Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allTraces.map((trace) => {
                      const isAlreadyInSession = existingTraceIds.has(trace.trace_id);
                      return (
                        <tr key={trace.trace_id} className={`border-b hover:bg-muted/30 ${isAlreadyInSession ? 'opacity-50' : ''}`}>
                          <td className="p-2">
                            <Checkbox
                              checked={selectedTraces.has(trace.trace_id)}
                              disabled={isAlreadyInSession}
                              onCheckedChange={(checked) => {
                                const newSelected = new Set(selectedTraces);
                                if (checked) {
                                  newSelected.add(trace.trace_id);
                                } else {
                                  newSelected.delete(trace.trace_id);
                                }
                                setSelectedTraces(newSelected);
                              }}
                            />
                          </td>
                          <td className="p-2 font-mono text-xs">
                            {trace.trace_id.slice(0, 8)}...
                            {isAlreadyInSession && (
                              <Badge variant="secondary" className="ml-2 text-xs">
                                Already added
                              </Badge>
                            )}
                          </td>
                          <td className="p-2">
                            <Badge variant={trace.status === 'OK' ? 'default' : 'destructive'}>
                              {trace.status || 'Unknown'}
                            </Badge>
                          </td>
                          <td className="p-2 text-xs text-muted-foreground">
                            {trace.timestamp_ms ? new Date(trace.timestamp_ms).toLocaleString() : '-'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}