import React, { useState, useMemo, useEffect, useRef } from "react";
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
import { LabelSchemaFieldPreview } from "@/components/LabelSchemaFieldPreview";
import { Accordion } from "@/components/ui/accordion";
import {
  Plus,
  Info,
  ExternalLink,
  BarChart3,
  Eye,
  Trash2,
  Tag,
  X,
  Check,
} from "lucide-react";
import { ReviewApp, LabelingSession, LabelingSchema } from "@/types/renderers";
import { LabelingSchemaRef } from "@/fastapi_client/models/LabelingSchemaRef";
import {
  useLabelingSessions,
  useCreateLabelingSession,
  useDeleteLabelingSession,
  useUpdateLabelingSession,
  useLabelingItems,
  useSessionTraces,
  useSearchTraces,
  useLabelSchemas,
  queryKeys,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { mergeItemsWithTraces } from "@/utils/trace-merge-utils";

// Wrapper component to fetch items data for LabelingSessionItemsTable
function SessionItemsWrapper({
  reviewAppId,
  sessionId,
  reviewApp,
  session,
}: {
  reviewAppId: string;
  sessionId: string;
  reviewApp: ReviewApp | null | undefined;
  session: LabelingSession;
}) {
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
        rootMargin: "100px", // Start loading 100px before the element comes into view
      }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  const { data: itemsData, isLoading: isLoadingItems } = useLabelingItems(
    reviewAppId,
    sessionId,
    isVisible && !!reviewAppId && !!sessionId
  );

  // Fetch traces for merging (only for preview display)
  const { data: tracesData } = useSessionTraces(
    sessionId,
    session?.mlflow_run_id,
    isVisible && !!session?.mlflow_run_id && !!sessionId
  );

  // Merge items with trace previews
  const mergedItems = React.useMemo(() => {
    if (!itemsData?.items) return [];
    return mergeItemsWithTraces(itemsData.items, tracesData?.traces);
  }, [itemsData?.items, tracesData?.traces]);

  const isLoading = isLoadingItems;

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
          items={mergedItems}
          reviewApp={reviewApp}
          reviewAppId={reviewAppId}
          sessionId={sessionId}
          session={session}
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
            {selectedTraceId && <TraceExplorer traceId={selectedTraceId} />}
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

  // Add user state
  const [addingUserSessionId, setAddingUserSessionId] = useState<string | null>(null);
  const [newUserInput, setNewUserInput] = useState("");

  // Remove user confirmation dialog
  const [removeUserConfirmDialog, setRemoveUserConfirmDialog] = useState<{
    sessionId: string;
    userEmail: string;
  } | null>(null);

  // Get highlighted session ID from URL params
  const highlightSessionId = searchParams.get("highlight");

  // Fetch labeling sessions - only when this component is rendered
  const { data: sessionsData, isLoading: isLoadingSessions } = useLabelingSessions(
    !!reviewApp?.review_app_id
  );

  // Fetch available label schemas
  const { data: labelSchemas } = useLabelSchemas();

  // Create labeling session mutation
  const createSessionMutation = useCreateLabelingSession();

  // Delete labeling session mutation
  const deleteSessionMutation = useDeleteLabelingSession();

  // Update labeling session mutation
  const updateSessionMutation = useUpdateLabelingSession();

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
    const userEmails = assignedUsers ? assignedUsers.split(",").map((email: string) => email.trim()) : [];
    const currentUserEmail = currentUser?.emails?.[0] || currentUser?.userName;
    if (currentUserEmail && !userEmails.includes(currentUserEmail)) {
      userEmails.push(currentUserEmail);
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

  const handleStartAddUser = (sessionId: string) => {
    setAddingUserSessionId(sessionId);
    setNewUserInput("");
  };

  const handleSaveNewUser = async (sessionId: string) => {
    if (!reviewApp?.review_app_id || !newUserInput.trim()) return;

    // Get current session data
    const session = sessionsData?.labeling_sessions?.find(
      (s: LabelingSession) => s.labeling_session_id === sessionId
    );
    if (!session) return;

    const newEmail = newUserInput.trim();
    const currentUsers = session.assigned_users || [];

    // Check if user already exists
    if (currentUsers.includes(newEmail)) {
      toast.error("User is already assigned to this session");
      return;
    }

    const updatedUsers = [...currentUsers, newEmail];

    try {
      await updateSessionMutation.mutateAsync({
        reviewAppId: reviewApp.review_app_id,
        sessionId,
        session: {
          name: session.name, // Include required name field
          assigned_users: updatedUsers,
        },
        updateMask: "assigned_users",
      });

      setAddingUserSessionId(null);
      setNewUserInput("");
      toast.success("User added successfully");
    } catch (error) {
      console.error("Failed to add user:", error);
      toast.error("Failed to add user");
    }
  };

  const handleCancelAddUser = () => {
    setAddingUserSessionId(null);
    setNewUserInput("");
  };

  const handleRemoveUser = async (sessionId: string, userEmail: string) => {
    if (!reviewApp?.review_app_id) return;

    // Get current session data
    const session = sessionsData?.labeling_sessions?.find(
      (s: LabelingSession) => s.labeling_session_id === sessionId
    );
    if (!session) return;

    const updatedUsers = (session.assigned_users || []).filter((email: string) => email !== userEmail);

    try {
      await updateSessionMutation.mutateAsync({
        reviewAppId: reviewApp.review_app_id,
        sessionId,
        session: {
          name: session.name, // Include required name field
          assigned_users: updatedUsers,
        },
        updateMask: "assigned_users",
      });

      setRemoveUserConfirmDialog(null);
      toast.success("User removed successfully");
    } catch (error) {
      console.error("Failed to remove user:", error);
      toast.error("Failed to remove user");
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
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
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
                  <div className="border rounded-lg p-4 max-h-[400px] overflow-y-auto space-y-4">
                    {[...labelSchemas]
                      .sort((a: LabelingSchema, b: LabelingSchema) => (a.title || a.name).localeCompare(b.title || b.name))
                      .map((schema: LabelingSchema) => (
                        <div key={schema.name} className="relative">
                          <div className="absolute left-2 top-3 z-10">
                            <Checkbox
                              id={`schema-select-${schema.name}`}
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
                          </div>
                          <div className="ml-8">
                            <Accordion type="single" collapsible className="w-full">
                              <LabelSchemaFieldPreview schema={schema} />
                            </Accordion>
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
                    {selectedSchemas.size} schema{selectedSchemas.size !== 1 ? "s" : ""} selected
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
                  Current user ({currentUser?.emails?.[0] || currentUser?.userName || "unknown"})
                  will be automatically added
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreateSession}
                disabled={
                  !newSessionName || selectedSchemas.size === 0 || createSessionMutation.isPending
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
            .sort((a: LabelingSession, b: LabelingSession) => new Date(b.create_time).getTime() - new Date(a.create_time).getTime())
            .map((session: LabelingSession) => {
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
                      <div>
                        Created {new Date(session.create_time).toLocaleDateString()} by{" "}
                        {session.created_by}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="text-xs text-muted-foreground">assigned users</div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-4 w-4 p-0 text-muted-foreground hover:text-green-600"
                            onClick={() => handleStartAddUser(session.labeling_session_id)}
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>

                        {addingUserSessionId === session.labeling_session_id ? (
                          <div className="flex items-center gap-2 mb-2">
                            <Input
                              type="email"
                              value={newUserInput}
                              onChange={(e) => setNewUserInput(e.target.value)}
                              placeholder="user@example.com"
                              className="h-7 text-xs"
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  handleSaveNewUser(session.labeling_session_id);
                                } else if (e.key === "Escape") {
                                  handleCancelAddUser();
                                }
                              }}
                            />
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-green-600"
                              onClick={() => handleSaveNewUser(session.labeling_session_id)}
                              disabled={!newUserInput.trim()}
                            >
                              <Check className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-red-600"
                              onClick={handleCancelAddUser}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ) : null}

                        <div className="flex flex-wrap gap-1">
                          {session.assigned_users && session.assigned_users.length > 0 ? (
                            session.assigned_users.map((user: string, index: number) => (
                              <Badge
                                key={index}
                                variant="outline"
                                className="text-xs pr-1 flex items-center gap-1"
                              >
                                <span>{user}</span>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-3 w-3 p-0 ml-1 text-muted-foreground rounded-full"
                                  onClick={() =>
                                    setRemoveUserConfirmDialog({
                                      sessionId: session.labeling_session_id,
                                      userEmail: user,
                                    })
                                  }
                                >
                                  <X className="h-2 w-2" />
                                </Button>
                              </Badge>
                            ))
                          ) : (
                            <div className="text-xs text-muted-foreground italic">
                              No users assigned
                            </div>
                          )}
                        </div>
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-4">
                      {session.labeling_schemas && session.labeling_schemas.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Selected Schemas</div>
                          <div className="flex flex-wrap gap-2">
                            {session.labeling_schemas.map((schema: LabelingSchemaRef, index: number) => (
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
                        session={session}
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
        sessionId={selectedAnalysisSession?.labeling_session_id || ""}
        sessionName={selectedAnalysisSession?.name || ""}
        reviewAppId={reviewApp?.review_app_id || ""}
        workspaceUrl={workspaceData?.workspace?.url}
        mlflowRunId={selectedAnalysisSession?.mlflow_run_id}
        experimentId={experimentId}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialog !== null} onOpenChange={() => setDeleteConfirmDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Labeling Session</DialogTitle>
            <DialogDescription>
              <div className="space-y-2">
                <p>
                  Are you sure you want to delete this labeling session? This action cannot be
                  undone.
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

      {/* Remove User Confirmation Dialog */}
      <Dialog
        open={removeUserConfirmDialog !== null}
        onOpenChange={() => setRemoveUserConfirmDialog(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove User</DialogTitle>
            <DialogDescription>
              <div className="space-y-2">
                <p>
                  Are you sure you want to remove{" "}
                  <strong>{removeUserConfirmDialog?.userEmail}</strong> from this labeling session?
                </p>
                <p className="text-sm text-muted-foreground">
                  This will remove their access to the session but keep any existing labels they've
                  provided.
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemoveUserConfirmDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                removeUserConfirmDialog &&
                handleRemoveUser(
                  removeUserConfirmDialog.sessionId,
                  removeUserConfirmDialog.userEmail
                )
              }
              disabled={updateSessionMutation.isPending}
            >
              {updateSessionMutation.isPending ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <X className="h-4 w-4 mr-2" />
              )}
              Remove User
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
  const [page, setPage] = useState(0);
  const [allTraces, setAllTraces] = useState<any[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
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

  // Search traces - Always enabled but we control when we want fresh data
  const {
    data: tracesData,
    isLoading: isLoadingTraces,
    isFetching,
    refetch,
  } = useSearchTraces({
    experiment_ids: experimentId ? [experimentId] : [],
    filter: searchFilter || undefined,
    max_results: 50,
    include_spans: false,
  });

  // Update allTraces when new data arrives (for infinite scroll)
  React.useEffect(() => {
    if (tracesData?.traces) {
      if (page === 0) {
        setAllTraces(tracesData.traces);
      } else {
        setAllTraces((prev) => [...prev, ...tracesData.traces]);
      }
    }
  }, [tracesData, page]);

  // Handle scroll to load more
  React.useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      // If we're within 100px of the bottom and not currently fetching, load more
      if (
        scrollHeight - scrollTop <= clientHeight + 100 &&
        !isFetching &&
        tracesData?.traces?.length === 50
      ) {
        loadMoreTraces();
      }
    };

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [isFetching, tracesData]);

  const traces = allTraces;

  // Load more traces
  const loadMoreTraces = () => {
    setPage((prev) => prev + 1);
    // In a real implementation with page tokens, we'd pass the token to the query
    // For now, this will just refetch the same data
    refetch();
  };

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

  const handleSearch = () => {
    setPage(0);
    setAllTraces([]);
    setSelectedTraces(new Set());
    refetch();
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <Plus className="h-4 w-4 mr-1" />
        Add Traces
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Add Traces to Session</DialogTitle>
            <DialogDescription>
              Search for traces and add them to "{session?.name || "this session"}"
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-hidden flex flex-col space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Enter filter (e.g., attributes.status = 'SUCCESS')"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSearch();
                  }
                }}
              />
              <Button onClick={handleSearch}>Search</Button>
            </div>

            {/* Traces table */}
            <div className="border rounded-lg flex-1 overflow-auto" ref={scrollContainerRef}>
              {isLoadingTraces ? (
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr className="border-b">
                      <th className="text-left p-2 font-medium">
                        <Skeleton className="h-4 w-4" />
                      </th>
                      <th className="text-left p-2 font-medium">Trace ID</th>
                      <th className="text-left p-2 font-medium">Request</th>
                      <th className="text-left p-2 font-medium">Response</th>
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
                          <Skeleton className="h-4 w-32" />
                        </td>
                        <td className="p-2">
                          <Skeleton className="h-4 w-32" />
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
              ) : traces.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  No traces found{searchFilter ? " matching your search" : ""}
                </div>
              ) : (
                <table className="w-full min-w-[800px]">
                  <thead className="sticky top-0 bg-background z-10 border-b">
                    <tr>
                      <th className="text-left p-2 w-10">
                        <Checkbox
                          checked={
                            traces.length > 0 &&
                            selectedTraces.size ===
                              traces.filter(
                                (t) => t.info?.trace_id && !existingTraceIds.has(t.info.trace_id)
                              ).length
                          }
                          onCheckedChange={(checked) => {
                            if (checked) {
                              const availableTraces = traces.filter(
                                (t) => t.info?.trace_id && !existingTraceIds.has(t.info.trace_id)
                              );
                              setSelectedTraces(
                                new Set(availableTraces.map((t) => t.info.trace_id))
                              );
                            } else {
                              setSelectedTraces(new Set());
                            }
                          }}
                        />
                      </th>
                      <th className="text-left p-2 font-medium min-w-[120px]">Trace ID</th>
                      <th className="text-left p-2 font-medium min-w-[250px]">Request</th>
                      <th className="text-left p-2 font-medium min-w-[250px]">Response</th>
                      <th className="text-left p-2 font-medium min-w-[80px]">Status</th>
                      <th className="text-left p-2 font-medium min-w-[150px]">Start Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traces.map((trace) => {
                      const traceId = trace.info?.trace_id;
                      const isAlreadyInSession = traceId && existingTraceIds.has(traceId);
                      return (
                        <tr
                          key={traceId || Math.random()}
                          className={`border-b hover:bg-muted/30 ${isAlreadyInSession ? "opacity-50" : ""}`}
                        >
                          <td className="p-2 w-10">
                            <Checkbox
                              checked={traceId && selectedTraces.has(traceId)}
                              disabled={!traceId || isAlreadyInSession}
                              onCheckedChange={(checked) => {
                                if (!traceId) return;
                                const newSelected = new Set(selectedTraces);
                                if (checked) {
                                  newSelected.add(traceId);
                                } else {
                                  newSelected.delete(traceId);
                                }
                                setSelectedTraces(newSelected);
                              }}
                            />
                          </td>
                          <td className="p-2 font-mono text-xs min-w-[120px]">
                            <div className="truncate" title={traceId}>
                              {traceId ? `${traceId.slice(0, 8)}...` : "No ID"}
                            </div>
                            {isAlreadyInSession && (
                              <Badge variant="secondary" className="mt-1 text-xs">
                                Already added
                              </Badge>
                            )}
                          </td>
                          <td className="p-2 text-xs min-w-[250px]">
                            <div className="truncate" title={trace.info?.request_preview}>
                              {trace.info?.request_preview || "-"}
                            </div>
                          </td>
                          <td className="p-2 text-xs min-w-[250px]">
                            <div className="truncate" title={trace.info?.response_preview}>
                              {trace.info?.response_preview || "-"}
                            </div>
                          </td>
                          <td className="p-2 min-w-[80px]">
                            <Badge variant={trace.info?.state === "OK" ? "default" : "destructive"}>
                              {trace.info?.state || "Unknown"}
                            </Badge>
                          </td>
                          <td className="p-2 text-xs text-muted-foreground min-w-[150px]">
                            {trace.info?.request_time
                              ? new Date(parseInt(trace.info.request_time)).toLocaleString()
                              : "-"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
              {/* Loading more indicator */}
              {isFetching && page > 0 && (
                <div className="p-4 text-center border-t">
                  <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Loading more traces...
                  </div>
                </div>
              )}
              {/* Load more button (as fallback if scroll doesn't work) */}
              {!isFetching && tracesData?.traces?.length === 50 && traces.length > 0 && (
                <div className="p-4 text-center border-t">
                  <Button variant="outline" size="sm" onClick={loadMoreTraces}>
                    Load More Traces
                  </Button>
                </div>
              )}
            </div>

            {/* Footer with selection count and link button */}
            <div className="flex items-center justify-between pt-4 border-t">
              <span className="text-sm text-muted-foreground">
                {selectedTraces.size > 0
                  ? `${selectedTraces.size} trace${selectedTraces.size !== 1 ? "s" : ""} selected`
                  : "No traces selected"}
              </span>
              <Button
                onClick={handleLinkTraces}
                disabled={selectedTraces.size === 0 || linkTracesMutation.isPending}
              >
                {linkTracesMutation.isPending ? "Linking..." : "Link Selected Traces"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
