import { useState, useEffect, useRef, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { ExperimentAnalysis } from "@/components/ExperimentAnalysis";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { SchemaButton } from "@/components/SchemaButton";
import { LabelingSessionItemsTable } from "@/components/LabelingSessionItemsTable";
import { TraceExplorer } from "@/components/TraceExplorer";
import { LabelingSessionAnalysisModal } from "@/components/LabelingSessionAnalysisModal";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Edit,
  Users,
  FileText,
  Activity,
  Database,
  ExternalLink,
  Settings,
  Save,
  X,
  Info,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Search,
  Eye,
  BarChart3,
} from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import {
  useConfig,
  useCurrentReviewApp,
  useLabelingSessions,
  useCreateLabelingSession,
  useExperiment,
  useExperimentSummary,
  useLabelingItems,
  useCurrentUser,
  useSearchTraces,
  useUpdateReviewApp,
  queryKeys,
} from "@/hooks/api-hooks";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

export function DeveloperDashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isCreateSessionOpen, setIsCreateSessionOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState("");
  const [assignedUsers, setAssignedUsers] = useState("");
  const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());

  // Analysis modal state
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [selectedAnalysisSession, setSelectedAnalysisSession] = useState<any>(null);
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

  // Get highlighted session ID from URL params
  const highlightSessionId = searchParams.get("highlight");

  // Schema refs for scrolling
  const schemaRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Schema editing state
  const [editingSchemas, setEditingSchemas] = useState<Record<string, any>>({});
  const [savingSchemas, setSavingSchemas] = useState<Set<string>>(new Set());
  const [deletingSchemas, setDeletingSchemas] = useState<Set<string>>(new Set());
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<string | null>(null);

  // Get experiment ID from config
  const { data: configData } = useConfig();
  const EXPERIMENT_ID = configData?.experiment_id;

  // Get workspace info
  const { data: workspaceData } = useQuery({
    queryKey: ["workspace"],
    queryFn: () => apiClient.api.getUserWorkspace(),
  });

  // Get current user
  const { data: currentUser } = useCurrentUser();

  // Get experiment info
  const { data: experimentData } = useExperiment(EXPERIMENT_ID || "", !!EXPERIMENT_ID);

  // Get experiment summary
  const { data: experimentSummary, isLoading: isLoadingSummary } = useExperimentSummary(
    EXPERIMENT_ID || "",
    !!EXPERIMENT_ID
  );

  // Get current review app
  const { data: reviewApp, isLoading: isLoadingReviewApps } = useCurrentReviewApp();
  const updateReviewAppMutation = useUpdateReviewApp();

  // Get labeling sessions
  const { data: sessionsData, isLoading: isLoadingSessions } = useLabelingSessions(
    reviewApp?.review_app_id || "",
    !!reviewApp?.review_app_id
  );

  // Create labeling session mutation
  const createSessionMutation = useCreateLabelingSession();

  // Schema editing functions
  const initializeSchemaForEditing = (schema: any) => {
    if (!editingSchemas[schema.name]) {
      setEditingSchemas((prev) => ({
        ...prev,
        [schema.name]: { ...schema },
      }));
    }
  };

  const updateEditingSchema = (schemaName: string, updates: any) => {
    setEditingSchemas((prev) => ({
      ...prev,
      [schemaName]: { ...prev[schemaName], ...updates },
    }));
  };

  // Helper function to count how many labeling sessions use a specific schema
  const getSchemaUsageCount = (schemaName: string) => {
    if (!sessionsData?.labeling_sessions) return 0;

    return sessionsData.labeling_sessions.filter((session) =>
      session.labeling_schemas?.some((sessionSchema) => sessionSchema.name === schemaName)
    ).length;
  };

  // Helper function to get session names using a specific schema
  const getSessionsUsingSchema = (schemaName: string) => {
    if (!sessionsData?.labeling_sessions) return [];

    return sessionsData.labeling_sessions
      .filter((session) =>
        session.labeling_schemas?.some((sessionSchema) => sessionSchema.name === schemaName)
      )
      .map((session) => session.name);
  };

  const getSchemaType = (schema: any) => {
    if (schema.categorical) {
      const options = schema.categorical.options || [];
      if (options.length === 2) {
        const lowerOptions = options.map((opt: string) => opt.toLowerCase());
        if (lowerOptions.includes("yes") && lowerOptions.includes("no")) {
          return "pass_fail";
        }
      }
      return "categorical";
    }
    if (schema.text) return "text";
    if (schema.numeric) return "numeric";
    return "text";
  };

  const handleSchemaTypeChange = (schemaName: string, newType: string) => {
    const newSchema: any = { ...editingSchemas[schemaName] };

    // Clear existing schema type fields
    newSchema.categorical = undefined;
    newSchema.text = undefined;
    newSchema.numeric = undefined;

    // Set defaults for new type
    if (newType === "text") {
      newSchema.text = { max_length: 500 };
    } else if (newType === "categorical") {
      newSchema.categorical = { options: ["Option 1", "Option 2"] };
    } else if (newType === "numeric") {
      newSchema.numeric = { min_value: 1, max_value: 5 };
    } else if (newType === "pass_fail") {
      newSchema.categorical = { options: ["Yes", "No"] };
    }

    setEditingSchemas((prev) => ({
      ...prev,
      [schemaName]: newSchema,
    }));
  };

  const handleSaveSchema = async (schemaName: string) => {
    setSavingSchemas((prev) => new Set([...prev, schemaName]));
    try {
      // Here you would call your update schema API
      console.log("Saving schema:", editingSchemas[schemaName]);
      // await apiClient.api.updateSchema(editingSchemas[schemaName]);
    } catch (error) {
      console.error("Failed to save schema:", error);
    } finally {
      setSavingSchemas((prev) => {
        const newSet = new Set(prev);
        newSet.delete(schemaName);
        return newSet;
      });
    }
  };

  const handleDeleteSchema = (schemaName: string) => {
    setDeleteConfirmDialog(schemaName);
  };

  const confirmDeleteSchema = async (schemaName: string) => {
    setDeletingSchemas((prev) => new Set([...prev, schemaName]));
    try {
      // Here you would call your delete schema API
      console.log("Deleting schema:", schemaName);
      // await apiClient.api.deleteSchema(schemaName);

      // Simulate successful deletion by invalidating queries
      queryClient.invalidateQueries({ queryKey: ["reviewApps"] });
      queryClient.invalidateQueries({ queryKey: ["labelingSessions"] });

      // Clear the editing state for this schema
      setEditingSchemas((prev) => {
        const updated = { ...prev };
        delete updated[schemaName];
        return updated;
      });
    } catch (error) {
      console.error("Failed to delete schema:", error);
    } finally {
      setDeletingSchemas((prev) => {
        const newSet = new Set(prev);
        newSet.delete(schemaName);
        return newSet;
      });
      setDeleteConfirmDialog(null);
    }
  };

  // Handle deep linking to schemas
  useEffect(() => {
    const hash = window.location.hash.replace("#", "");
    if (hash.startsWith("schema-")) {
      const schemaName = hash.replace("schema-", "");
      // Switch to schemas tab
      handleTabChange("schemas");
      // Scroll to schema after a short delay
      setTimeout(() => {
        const schemaElement = schemaRefs.current[schemaName];
        if (schemaElement) {
          schemaElement.scrollIntoView({ behavior: "smooth", block: "center" });
          // Add temporary highlight
          schemaElement.classList.add("ring-2", "ring-blue-500", "ring-offset-2");
          setTimeout(() => {
            schemaElement.classList.remove("ring-2", "ring-blue-500", "ring-offset-2");
          }, 3000);
        }
      }, 100);
    }
  }, [handleTabChange]);

  // Function to handle schema badge clicks
  const handleSchemaClick = (schemaName: string) => {
    // Update URL hash
    window.location.hash = `schema-${schemaName}`;
    // Switch to schemas tab
    handleTabChange("schemas");
    // Scroll to schema
    setTimeout(() => {
      const schemaElement = schemaRefs.current[schemaName];
      if (schemaElement) {
        schemaElement.scrollIntoView({ behavior: "smooth", block: "center" });
        // Add temporary highlight
        schemaElement.classList.add("ring-2", "ring-blue-500", "ring-offset-2");
        setTimeout(() => {
          schemaElement.classList.remove("ring-2", "ring-blue-500", "ring-offset-2");
        }, 3000);
      }
    }, 100);
  };

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

    // Require at least the current user if no users specified
    if (userEmails.length === 0 && currentUser?.email) {
      userEmails = [currentUser.email];
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
        },
      }
    );
  };

  if (isLoadingReviewApps || isLoadingSessions) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-3xl font-bold">Developer Dashboard</h1>
          </div>
          <p className="text-muted-foreground mt-1">
            Manage review apps, labeling sessions, and monitor progress
          </p>
        </div>

        {/* Databricks Links - Right Side */}
        <div className="bg-muted/30 rounded-lg p-4 ml-6 min-w-96">
          <div className="flex items-center gap-2 mb-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Databricks Links
            </span>
          </div>

          <div className="flex items-center gap-6 mb-3">
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
                        {experimentData?.experiment?.name || "Loading..."}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Experiment ID: {EXPERIMENT_ID}
                      </p>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            {reviewApp && (
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
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList>
          <TabsTrigger value="sessions" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Labeling Sessions
          </TabsTrigger>
          <TabsTrigger value="schemas" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Label Schemas
          </TabsTrigger>
          <TabsTrigger value="summary" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Experiment Summary
          </TabsTrigger>
        </TabsList>

        {/* Labeling Sessions Tab */}
        <TabsContent value="sessions" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Labeling Sessions</h2>
            <Dialog
              open={isCreateSessionOpen}
              onOpenChange={(open) => {
                setIsCreateSessionOpen(open);
                // Reset selected schemas when dialog opens
                if (open && reviewApp?.labeling_schemas) {
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
                    {reviewApp?.labeling_schemas && reviewApp.labeling_schemas.length > 0 ? (
                      <div className="border rounded-lg p-4 max-h-60 overflow-y-auto space-y-3">
                        {reviewApp.labeling_schemas.map((schema) => (
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
                            <div className="flex-1">
                              <label
                                htmlFor={`schema-${schema.name}`}
                                className="text-sm font-medium cursor-pointer"
                              >
                                {schema.title || schema.name}
                              </label>
                              {schema.instruction && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  {schema.instruction}
                                </p>
                              )}
                              <div className="flex gap-2 mt-1">
                                {schema.type && (
                                  <Badge variant="outline" className="text-xs">
                                    {schema.type}
                                  </Badge>
                                )}
                                {schema.categorical && (
                                  <Badge variant="secondary" className="text-xs">
                                    {schema.categorical.options?.length} options
                                  </Badge>
                                )}
                                {schema.numeric && (
                                  <Badge variant="secondary" className="text-xs">
                                    Numeric
                                  </Badge>
                                )}
                                {schema.text && (
                                  <Badge variant="secondary" className="text-xs">
                                    Text
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="border rounded-lg p-4 text-center text-muted-foreground">
                        No labeling schemas available. Please create schemas first.
                      </div>
                    )}
                    {selectedSchemas.size > 0 && (
                      <p className="text-sm text-muted-foreground">
                        {selectedSchemas.size} schema{selectedSchemas.size !== 1 ? "s" : ""}{" "}
                        selected
                      </p>
                    )}
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="users">Assigned Users</Label>
                    <Input
                      id="users"
                      value={assignedUsers}
                      onChange={(e) => setAssignedUsers(e.target.value)}
                      placeholder="user1@example.com, user2@example.com"
                    />
                    <p className="text-sm text-muted-foreground">
                      Comma-separated list of email addresses
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
                      className={isHighlighted ? "border-2 border-blue-500 shadow-lg" : ""}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-lg">{session.name}</CardTitle>
                            <CardDescription className="text-xs flex items-center gap-3 mt-1">
                              <span>
                                Created {new Date(session.create_time).toLocaleDateString()} by{" "}
                                {session.created_by}
                              </span>
                              {workspaceData?.workspace?.url && (
                                <>
                                  <a
                                    href={`${workspaceData.workspace.url}/ml/experiments/${EXPERIMENT_ID}/labeling-sessions?selectedLabelingSessionId=${session.labeling_session_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                                    title="View Session in Databricks"
                                  >
                                    Session
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                  <a
                                    href={`${workspaceData.workspace.url}/ml/experiments/${EXPERIMENT_ID}/evaluation-runs?selectedRunUuid=${session.mlflow_run_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                                    title="View MLflow Run in Databricks"
                                  >
                                    Run
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                </>
                              )}
                            </CardDescription>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedAnalysisSession(session);
                                setAnalysisModalOpen(true);
                              }}
                            >
                              <BarChart3 className="h-4 w-4 mr-1" />
                              Analysis
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/preview/${session.labeling_session_id}`)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Preview
                            </Button>
                            <AddTracesButton
                              reviewAppId={reviewApp?.review_app_id || ""}
                              sessionId={session.labeling_session_id}
                              session={session}
                              experimentId={EXPERIMENT_ID || ""}
                            />
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        {/* Labeling Schemas - Primary Focus */}
                        {session.labeling_schemas && session.labeling_schemas.length > 0 && (
                          <div className="mb-4">
                            <p className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1">
                              <FileText className="h-4 w-4" />
                              Labeling Schemas
                            </p>
                            <div className="flex gap-2 flex-wrap">
                              {session.labeling_schemas.map((schema, idx) => (
                                <SchemaButton
                                  key={idx}
                                  schema={schema}
                                  onClick={handleSchemaClick}
                                  className="h-7"
                                />
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Progress Section - Secondary Focus */}
                        <SessionProgress
                          reviewAppId={reviewApp?.review_app_id || ""}
                          sessionId={session.labeling_session_id}
                          reviewApp={reviewApp}
                          workspaceUrl={workspaceData?.workspace?.url}
                        />

                        {/* Compact Users Info */}
                        {session.assigned_users && session.assigned_users.length > 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Users className="h-3 w-3" />
                              <span>{session.assigned_users.join(", ")}</span>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Labeling Sessions</CardTitle>
                <CardDescription>
                  Create your first labeling session to start reviewing traces.
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>

        {/* Label Schemas Tab */}
        <TabsContent value="schemas" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Label Schemas</h2>
            <Button
              onClick={async () => {
                // Check if new_assessment schema already exists
                if (reviewApp?.labeling_schemas?.find(s => s.name === "new_assessment")) {
                  toast.info("Schema 'new_assessment' already exists");
                  return;
                }
                
                // Create new pass/fail schema
                const newSchema = {
                  name: "new_assessment",
                  title: "New Assessment",
                  instruction: "Does this pass or fail?",
                  type: "FEEDBACK",
                  categorical: {
                    options: ["Pass", "Fail"]
                  },
                  enable_comment: true
                };
                
                // Add to existing schemas
                const updatedSchemas = [...(reviewApp?.labeling_schemas || []), newSchema];
                
                try {
                  await updateReviewAppMutation.mutateAsync({
                    reviewAppId: reviewApp?.review_app_id || "",
                    reviewApp: {
                      labeling_schemas: updatedSchemas
                    },
                    updateMask: "labeling_schemas"
                  });
                  toast.success("Created new assessment schema");
                } catch (error) {
                  toast.error("Failed to create schema");
                  console.error(error);
                }
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Schema
            </Button>
          </div>

          {reviewApp?.labeling_schemas && reviewApp.labeling_schemas.length > 0 ? (
            <div className="space-y-6">
              {reviewApp.labeling_schemas.map((schema) => {
                // Initialize editing state for this schema
                initializeSchemaForEditing(schema);
                const editingSchema = editingSchemas[schema.name] || schema;
                const currentType = getSchemaType(editingSchema);
                const isSaving = savingSchemas.has(schema.name);
                const isDeleting = deletingSchemas.has(schema.name);
                const usageCount = getSchemaUsageCount(schema.name);
                const sessionsUsingSchema = getSessionsUsingSchema(schema.name);

                return (
                  <Card
                    key={schema.name}
                    className="border shadow-sm transition-all duration-300"
                    ref={(el) => {
                      schemaRefs.current[schema.name] = el;
                    }}
                  >
                    <CardContent className="p-6">
                      {/* Schema Name and Type Row */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <label className="text-sm font-medium">Assessment Name</label>
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>A unique identifier for this assessment</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                          <Input
                            value={editingSchema.name || ""}
                            onChange={(e) =>
                              updateEditingSchema(schema.name, { name: e.target.value })
                            }
                            placeholder="unique_assessment_key"
                          />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <label className="text-sm font-medium">Assessment Type</label>
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Choose feedback or expectations for reviewers</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                          <Select
                            value={editingSchema.type || "FEEDBACK"}
                            onValueChange={(value) =>
                              updateEditingSchema(schema.name, { type: value })
                            }
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="FEEDBACK">Feedback</SelectItem>
                              <SelectItem value="EXPECTATION">Expectation</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Schema Usage - Links to Sessions */}
                      {usageCount > 0 && (
                        <div className="mb-4 p-3 bg-muted/30 rounded-lg">
                          <p className="text-sm font-medium text-muted-foreground mb-2">
                            Used by {usageCount} labeling session{usageCount > 1 ? "s" : ""}:
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {sessionsData?.labeling_sessions
                              ?.filter((session) =>
                                session.labeling_schemas?.some(
                                  (sessionSchema) => sessionSchema.name === schema.name
                                )
                              )
                              .map((session) => (
                                <Button
                                  key={session.labeling_session_id}
                                  variant="outline"
                                  size="sm"
                                  className="h-8 px-3 text-xs"
                                  onClick={() =>
                                    navigate(`/preview/${session.labeling_session_id}`)
                                  }
                                >
                                  <Users className="h-3 w-3 mr-1" />
                                  {session.name}
                                </Button>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Title */}
                      <div className="mb-4">
                        <label className="text-sm font-medium mb-2 block">Title</label>
                        <Input
                          value={editingSchema.title || ""}
                          onChange={(e) =>
                            updateEditingSchema(schema.name, { title: e.target.value })
                          }
                          placeholder="Title shown to reviewers for this task"
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                          The title displayed to reviewers when completing this assessment
                        </p>
                      </div>

                      {/* Instructions */}
                      <div className="mb-4">
                        <label className="text-sm font-medium mb-2 block">Instructions</label>
                        <Textarea
                          value={editingSchema.instruction || ""}
                          onChange={(e) =>
                            updateEditingSchema(schema.name, { instruction: e.target.value })
                          }
                          placeholder="Instructions for reviewers on how to complete this task"
                          rows={2}
                        />
                      </div>

                      {/* Input Type */}
                      <div className="mb-4">
                        <label className="text-sm font-medium mb-2 block">Input Type</label>
                        <Select
                          value={currentType}
                          onValueChange={(value) => handleSchemaTypeChange(schema.name, value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pass_fail">Pass/Fail</SelectItem>
                            <SelectItem value="categorical">Categorical (Single Choice)</SelectItem>
                            <SelectItem value="text">Text</SelectItem>
                            <SelectItem value="numeric">Numeric</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Enable Comments */}
                      <div className="flex items-center space-x-2 mb-4">
                        <Checkbox
                          id={`enable-comment-${schema.name}`}
                          checked={editingSchema.enable_comment || false}
                          onCheckedChange={(checked) =>
                            updateEditingSchema(schema.name, { enable_comment: checked })
                          }
                        />
                        <label htmlFor={`enable-comment-${schema.name}`} className="text-sm">
                          Enable comments
                        </label>
                      </div>

                      {/* Type-specific editors */}
                      {currentType === "categorical" && currentType !== "pass_fail" && (
                        <div className="mb-4">
                          <label className="text-sm font-medium mb-2 block">Options</label>
                          <div className="space-y-2">
                            {(editingSchema.categorical?.options || []).map(
                              (option: string, index: number) => (
                                <div key={index} className="flex items-center gap-2">
                                  <Input
                                    value={option}
                                    onChange={(e) => {
                                      const newOptions = [
                                        ...(editingSchema.categorical?.options || []),
                                      ];
                                      newOptions[index] = e.target.value;
                                      updateEditingSchema(schema.name, {
                                        categorical: { options: newOptions },
                                      });
                                    }}
                                    placeholder={`Option ${index + 1}`}
                                  />
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      const newOptions = [
                                        ...(editingSchema.categorical?.options || []),
                                      ];
                                      newOptions.splice(index, 1);
                                      updateEditingSchema(schema.name, {
                                        categorical: { options: newOptions },
                                      });
                                    }}
                                    disabled={
                                      (editingSchema.categorical?.options || []).length <= 1
                                    }
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                              )
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                const newOptions = [
                                  ...(editingSchema.categorical?.options || []),
                                  `Option ${(editingSchema.categorical?.options || []).length + 1}`,
                                ];
                                updateEditingSchema(schema.name, {
                                  categorical: { options: newOptions },
                                });
                              }}
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              Add Option
                            </Button>
                          </div>
                        </div>
                      )}

                      {currentType === "numeric" && (
                        <div className="mb-4">
                          <label className="text-sm font-medium mb-2 block">Numeric Range</label>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="text-xs text-muted-foreground mb-1 block">
                                Min Value
                              </label>
                              <Input
                                type="number"
                                value={editingSchema.numeric?.min_value?.toString() || ""}
                                onChange={(e) => {
                                  const value = e.target.value
                                    ? parseFloat(e.target.value)
                                    : undefined;
                                  updateEditingSchema(schema.name, {
                                    numeric: { ...editingSchema.numeric, min_value: value },
                                  });
                                }}
                                placeholder="No minimum"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-muted-foreground mb-1 block">
                                Max Value
                              </label>
                              <Input
                                type="number"
                                value={editingSchema.numeric?.max_value?.toString() || ""}
                                onChange={(e) => {
                                  const value = e.target.value
                                    ? parseFloat(e.target.value)
                                    : undefined;
                                  updateEditingSchema(schema.name, {
                                    numeric: { ...editingSchema.numeric, max_value: value },
                                  });
                                }}
                                placeholder="No maximum"
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {currentType === "text" && (
                        <div className="mb-4">
                          <label className="text-sm font-medium mb-2 block">Text Settings</label>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">Max Length:</span>
                            <Input
                              type="number"
                              value={editingSchema.text?.max_length?.toString() || ""}
                              onChange={(e) => {
                                const value = e.target.value ? parseInt(e.target.value) : undefined;
                                updateEditingSchema(schema.name, {
                                  text: { max_length: value },
                                });
                              }}
                              placeholder="No limit"
                              className="w-32"
                            />
                          </div>
                        </div>
                      )}

                      {/* Save and Delete buttons */}
                      <div className="flex justify-end gap-2 pt-4 border-t">
                        <Button
                          variant="destructive"
                          onClick={() => handleDeleteSchema(schema.name)}
                          disabled={isDeleting}
                        >
                          {isDeleting ? (
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
                          ) : (
                            <Trash2 className="h-3 w-3 mr-2" />
                          )}
                          Delete
                        </Button>
                        <Button onClick={() => handleSaveSchema(schema.name)} disabled={isSaving}>
                          {isSaving ? (
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
                          ) : (
                            <Save className="h-3 w-3 mr-2" />
                          )}
                          Save
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Label Schemas</CardTitle>
                <CardDescription>
                  Create your first labeling schema to define evaluation criteria.
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>

        {/* Experiment Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <ExperimentAnalysis
            experimentId={EXPERIMENT_ID || ""}
            experimentSummary={experimentSummary}
            isLoadingSummary={isLoadingSummary}
          />
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialog !== null} onOpenChange={() => setDeleteConfirmDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Label Schema</DialogTitle>
            <DialogDescription>
              <div className="space-y-2">
                <p>
                  Are you sure you want to delete the schema "{deleteConfirmDialog}"? This action
                  cannot be undone.
                </p>
                {deleteConfirmDialog && (
                  <div className="bg-muted/50 rounded-lg p-3 mt-3">
                    <p className="text-sm font-medium mb-1">Usage Information:</p>
                    {getSchemaUsageCount(deleteConfirmDialog) === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        This schema is not currently used by any labeling sessions.
                      </p>
                    ) : (
                      <div className="text-sm">
                        <p className="text-orange-600 font-medium">
                          ⚠️ This schema is currently used by{" "}
                          {getSchemaUsageCount(deleteConfirmDialog)} labeling session
                          {getSchemaUsageCount(deleteConfirmDialog) > 1 ? "s" : ""}:
                        </p>
                        <ul className="list-disc list-inside mt-1 text-muted-foreground">
                          {getSessionsUsingSchema(deleteConfirmDialog).map((sessionName, idx) => (
                            <li key={idx}>{sessionName}</li>
                          ))}
                        </ul>
                        <p className="text-sm text-muted-foreground mt-2">
                          Deleting this schema may affect these sessions' evaluation criteria.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmDialog && confirmDeleteSchema(deleteConfirmDialog)}
              disabled={deletingSchemas.has(deleteConfirmDialog || "")}
            >
              {deletingSchemas.has(deleteConfirmDialog || "") ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Delete Schema
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Analysis Modal */}
      {selectedAnalysisSession && (
        <LabelingSessionAnalysisModal
          isOpen={analysisModalOpen}
          onClose={() => {
            setAnalysisModalOpen(false);
            setSelectedAnalysisSession(null);
          }}
          reviewAppId={reviewApp?.review_app_id || ""}
          sessionId={selectedAnalysisSession.labeling_session_id}
          sessionName={selectedAnalysisSession.name}
          workspaceUrl={workspaceData?.workspace?.url}
          mlflowRunId={selectedAnalysisSession.mlflow_run_id}
        />
      )}
    </div>
  );
}

// Global state to throttle lazy loading - prevent too many simultaneous requests
const globalLazyLoadState = {
  currentlyLoading: new Set<string>(),
  maxConcurrent: 1, // Only allow 1 concurrent request to be ultra-conservative
  queue: [] as { sessionId: string; trigger: () => void }[],
};

// Helper component to show progress for each labeling session
function SessionProgress({
  reviewAppId,
  sessionId,
  reviewApp,
  workspaceUrl,
}: {
  reviewAppId: string;
  sessionId: string;
  reviewApp: any;
  workspaceUrl?: string;
}) {
  const [shouldFetch, setShouldFetch] = useState(false);
  const [selectedTraceForModal, setSelectedTraceForModal] = useState<string | null>(null);
  const [isTraceModalOpen, setIsTraceModalOpen] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Debug logging for state changes
  useEffect(() => {
    console.log(
      `[LAZY-LOAD-STATE] Session ${sessionId.slice(0, 8)} shouldFetch changed to: ${shouldFetch}`
    );
  }, [shouldFetch, sessionId]);

  // Set up intersection observer for lazy loading - trigger when session progress section comes into view
  useEffect(() => {
    // Don't set up observer if we already fetched or don't have required IDs
    if (shouldFetch || !reviewAppId || !sessionId || !cardRef.current) {
      return;
    }

    // Small delay to ensure DOM is fully rendered before setting up observer
    const timeoutId = setTimeout(() => {
      if (!cardRef.current || shouldFetch) return;

      console.log(
        `[LAZY-LOAD] Setting up intersection observer for session ${sessionId.slice(0, 8)}`
      );

      // Clean up existing observer
      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      // Create new observer with VERY strict settings to prevent early triggering
      observerRef.current = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          console.log(
            `[LAZY-LOAD] Session ${sessionId.slice(0, 8)} intersection: ${entry.isIntersecting}, ratio: ${entry.intersectionRatio}, boundingRect top: ${entry.boundingClientRect.top}`
          );

          // MUCH stricter visibility check - require at least 25% visible AND not too close to top
          if (
            entry.isIntersecting &&
            entry.intersectionRatio >= 0.25 &&
            entry.boundingClientRect.top > 0
          ) {
            // Ensure it's not at the very top
            console.log(
              `[LAZY-LOAD] Session ${sessionId.slice(0, 8)} came into view - STRICT check passed`
            );

            // Throttling logic - prevent too many simultaneous requests
            const triggerFetch = () => {
              console.log(`[LAZY-LOAD] ✅ Triggering fetch for session ${sessionId.slice(0, 8)}`);
              globalLazyLoadState.currentlyLoading.add(sessionId);
              setShouldFetch(true);

              // Disconnect observer immediately after triggering
              if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
              }
            };

            // Check if we can load immediately or need to queue
            if (globalLazyLoadState.currentlyLoading.size < globalLazyLoadState.maxConcurrent) {
              triggerFetch();
            } else {
              console.log(
                `[LAZY-LOAD] 📋 Queuing session ${sessionId.slice(0, 8)} (${globalLazyLoadState.currentlyLoading.size} already loading)`
              );
              globalLazyLoadState.queue.push({ sessionId, trigger: triggerFetch });
            }
          } else {
            console.log(
              `[LAZY-LOAD] Session ${sessionId.slice(0, 8)} - visibility check FAILED (ratio: ${entry.intersectionRatio}, top: ${entry.boundingClientRect.top})`
            );
          }
        },
        {
          threshold: [0.25], // Require 25% of element to be visible
          rootMargin: "-50px", // Require element to be well within viewport
        }
      );

      observerRef.current.observe(cardRef.current);
    }, 250); // Longer delay to ensure layout is stable

    return () => {
      clearTimeout(timeoutId);
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
    };
  }, [sessionId, reviewAppId, shouldFetch]);

  // Early return if already fetched to prevent unnecessary renders
  const hasAlreadyFetched = shouldFetch;

  // Only fetch when explicitly enabled AND required fields are present
  const enableQuery = shouldFetch && !!reviewAppId && !!sessionId;

  // Debug logging for query enablement
  useEffect(() => {
    console.log(
      `[LAZY-LOAD-QUERY] Session ${sessionId.slice(0, 8)} enableQuery: ${enableQuery} (shouldFetch: ${shouldFetch}, hasIds: ${!!reviewAppId && !!sessionId})`
    );
  }, [enableQuery, shouldFetch, reviewAppId, sessionId]);

  const { data: itemsData, isLoading } = useLabelingItems(reviewAppId, sessionId, enableQuery);

  // Handle queue processing and cleanup when request completes
  useEffect(() => {
    if (!isLoading && shouldFetch && globalLazyLoadState.currentlyLoading.has(sessionId)) {
      // Request completed, remove from loading set
      globalLazyLoadState.currentlyLoading.delete(sessionId);
      console.log(
        `[LAZY-LOAD] Session ${sessionId.slice(0, 8)} completed loading, ${globalLazyLoadState.currentlyLoading.size} still loading`
      );

      // Process queue if there are waiting requests
      if (
        globalLazyLoadState.queue.length > 0 &&
        globalLazyLoadState.currentlyLoading.size < globalLazyLoadState.maxConcurrent
      ) {
        const next = globalLazyLoadState.queue.shift();
        if (next) {
          console.log(
            `[LAZY-LOAD] 🚀 Processing queued session ${next.sessionId.slice(0, 8)} (queue length: ${globalLazyLoadState.queue.length})`
          );
          next.trigger();
        }
      } else if (globalLazyLoadState.queue.length > 0) {
        console.log(
          `[LAZY-LOAD] ⏸️ Queue has ${globalLazyLoadState.queue.length} items but ${globalLazyLoadState.currentlyLoading.size} still loading`
        );
      }
    }
  }, [isLoading, shouldFetch, sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      globalLazyLoadState.currentlyLoading.delete(sessionId);
      globalLazyLoadState.queue = globalLazyLoadState.queue.filter(
        (q) => q.sessionId !== sessionId
      );
    };
  }, [sessionId]);

  const items = itemsData?.items || [];
  const completedCount = items.filter((i) => i.state === "COMPLETED").length;
  const progressPercentage = items.length > 0 ? (completedCount / items.length) * 100 : 0;

  return (
    <>
      <div className="mt-4 pt-4 border-t space-y-2" ref={cardRef}>
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Progress</span>
          <span className="text-sm">
            {!shouldFetch ? (
              <span className="text-muted-foreground">Scroll to load...</span>
            ) : (
              `${completedCount} / ${items.length} completed`
            )}
          </span>
        </div>
        <Progress value={!shouldFetch ? 0 : progressPercentage} className="h-2" />

        {/* Always show table */}
        <div className="mt-4">
          {!shouldFetch ? (
            <div className="border rounded-lg p-8 text-center text-muted-foreground">
              <div className="text-sm animate-pulse">Loading items...</div>
            </div>
          ) : isLoading ? (
            <div className="border rounded-lg p-8 text-center text-muted-foreground">
              <div className="animate-pulse">Loading items...</div>
            </div>
          ) : items.length === 0 ? (
            <div className="border rounded-lg p-8 text-center text-muted-foreground">
              <p>No items linked to this session</p>
              <p className="text-xs mt-1">Use the "Add Traces" button to add traces</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <LabelingSessionItemsTable
                items={items}
                reviewApp={reviewApp}
                reviewAppId={reviewAppId}
                sessionId={sessionId}
                onTraceClick={(traceId) => {
                  setSelectedTraceForModal(traceId);
                  setIsTraceModalOpen(true);
                }}
                showProgress={false} // Don't show progress again since we already have it above
                maxHeight="max-h-64" // Smaller height for embedded view
                showActions={true}
              />
            </div>
          )}
        </div>
      </div>

      {/* Trace Modal */}
      <Dialog open={isTraceModalOpen} onOpenChange={setIsTraceModalOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="flex-1 overflow-auto">
            {selectedTraceForModal && workspaceUrl && (
              <TraceExplorer
                traceId={selectedTraceForModal}
                experimentId={reviewApp?.experiment_id}
                databricksHost={workspaceUrl.replace("https://", "").replace("http://", "")}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// AddTracesButton component with modal containing trace search functionality
function AddTracesButton({
  reviewAppId,
  sessionId,
  session,
  experimentId,
}: {
  reviewAppId: string;
  sessionId: string;
  session: any;
  experimentId: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedTraces, setSelectedTraces] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [allTraces, setAllTraces] = useState<any[]>([]);
  const queryClient = useQueryClient();

  // Get current items to check which traces are already in session
  // Only fetch when the modal is open - don't fetch eagerly for all sessions
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
      // Don't close modal - let user continue adding more traces
      // Refresh search to update "in session" status
      searchTraces();
      toast.success(
        `Successfully linked ${traceIds.length} trace${traceIds.length !== 1 ? "s" : ""} to the session`
      );
    },
    onError: (error: any) => {
      toast.error(`Failed to link traces: ${error.message}`);
    },
  });

  const handleSearch = () => {
    setCurrentPage(1);
    setAllTraces([]);
    searchTraces();
  };

  const handleLoadMore = () => {
    if (!isLoadingTraces && hasNextPage) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const handleSelectAll = () => {
    if (allTraces) {
      const selectableTraceIds = new Set(
        allTraces.filter((t) => !existingTraceIds.has(t.info.trace_id)).map((t) => t.info.trace_id)
      );
      setSelectedTraces(selectableTraceIds);
    }
  };

  const handleDeselectAll = () => {
    setSelectedTraces(new Set());
  };

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
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Add Traces to Session</DialogTitle>
            <DialogDescription>
              Search for traces and add them to "{session?.name || "this session"}"
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden flex flex-col space-y-4">
            {/* Search Controls */}
            <div className="flex gap-2">
              <Input
                placeholder="Enter filter (e.g., attributes.status = 'SUCCESS')"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              <Button onClick={handleSearch} disabled={isLoadingTraces}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </Button>
            </div>

            {/* Trace Results */}
            <div className="flex-1 overflow-hidden flex flex-col">
              {allTraces && allTraces.length > 0 && (
                <>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-muted-foreground">
                      Found {allTraces.length} traces {hasNextPage && "(more available)"}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={handleSelectAll}>
                        Select All
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleDeselectAll}>
                        Deselect All
                      </Button>
                    </div>
                  </div>

                  <div className="flex-1 border rounded-lg overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12"></TableHead>
                          <TableHead>Time</TableHead>
                          <TableHead>Request</TableHead>
                          <TableHead>Response</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Duration</TableHead>
                          <TableHead>In Session</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {allTraces.map((trace) => (
                          <SearchTraceRow
                            key={trace.info.trace_id}
                            trace={trace}
                            selectedTraces={selectedTraces}
                            setSelectedTraces={setSelectedTraces}
                            isInSession={existingTraceIds.has(trace.info.trace_id)}
                          />
                        ))}
                        {/* Load more trigger */}
                        {hasNextPage && (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-4">
                              {isLoadingTraces ? (
                                <div className="animate-pulse">Loading more traces...</div>
                              ) : (
                                <Button variant="outline" onClick={handleLoadMore}>
                                  Load More
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </>
              )}

              {isLoadingTraces && currentPage === 1 && (
                <div className="text-center py-8 text-muted-foreground">Loading traces...</div>
              )}

              {!isLoadingTraces && allTraces?.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No traces found matching your search criteria
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleLinkTraces}
              disabled={linkTracesMutation.isPending || selectedTraces.size === 0}
            >
              {linkTracesMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Linking...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Link {selectedTraces.size} Trace{selectedTraces.size !== 1 ? "s" : ""} to Session
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Helper function to format relative time (reused from DevModeSessionManager)
function getRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return `${diffSeconds} second${diffSeconds !== 1 ? "s" : ""} ago`;
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes !== 1 ? "s" : ""} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
  } else {
    return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
  }
}

// Search trace row component (reused from DevModeSessionManager)
function SearchTraceRow({
  trace,
  selectedTraces,
  setSelectedTraces,
  isInSession = false,
}: {
  trace: any;
  selectedTraces: Set<string>;
  setSelectedTraces: (traces: Set<string>) => void;
  isInSession?: boolean;
}) {
  return (
    <TableRow className={`hover:bg-muted/50 ${isInSession ? "opacity-60" : ""}`}>
      <TableCell onClick={(e) => e.stopPropagation()}>
        <Checkbox
          checked={selectedTraces.has(trace.info.trace_id)}
          disabled={isInSession}
          onCheckedChange={(checked) => {
            if (isInSession) return;
            const newSelected = new Set(selectedTraces);
            if (checked) {
              newSelected.add(trace.info.trace_id);
            } else {
              newSelected.delete(trace.info.trace_id);
            }
            setSelectedTraces(newSelected);
          }}
        />
      </TableCell>
      <TableCell className="text-xs">
        {getRelativeTime(parseInt(trace.info.request_time) || Date.now())}
      </TableCell>
      <TableCell className="max-w-xs text-xs">
        <div className="text-left truncate block w-full" title={trace.info.request_preview || ""}>
          {trace.info.request_preview || "-"}
        </div>
      </TableCell>
      <TableCell className="max-w-xs truncate text-xs" title={trace.info.response_preview || ""}>
        {trace.info.response_preview || "-"}
      </TableCell>
      <TableCell>
        <Badge variant={trace.info.state === "SUCCESS" ? "default" : "destructive"}>
          {trace.info.state}
        </Badge>
      </TableCell>
      <TableCell className="text-xs">{trace.info.execution_duration}</TableCell>
      <TableCell>{isInSession ? <Checkbox checked disabled /> : <span></span>}</TableCell>
    </TableRow>
  );
}
