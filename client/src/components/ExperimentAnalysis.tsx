import React, { useState } from "react";
import { Markdown } from "@/components/ui/markdown";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BookOpen,
  AlertCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Tag,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Brain,
  ClipboardList,
  Save,
  Check,
  ExternalLink,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { ReviewAppsService } from "@/fastapi_client";
import { SchemaPreview } from "./SchemaPreview";
import { toast } from "sonner";
import {
  useAppManifest,
  useExperimentAnalysisStatus,
  useExperimentSummary,
  useTriggerExperimentAnalysis,
} from "@/hooks/api-hooks";

interface Schema {
  key: string;
  name: string;
  label_type: "FEEDBACK" | "EXPECTATION" | "NOT_SPECIFIED";
  schema_type: string;
  description: string;
  rationale?: string;
  priority_score?: number;
  grounded_in_traces?: string[];
  title?: string;
  instruction?: string;
  min?: number;
  max?: number;
  options?: string[];
  max_length?: number;
  enable_comment?: boolean;
}

interface Issue {
  issue_type: string;
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  description: string;
  affected_traces: number;
  example_traces?: string[];
  problem_snippets?: string[];
}

interface ExperimentAnalysisProps {
  experimentId: string;
}

export const ExperimentAnalysis: React.FC<ExperimentAnalysisProps> = ({
  experimentId,
}) => {
  // Fetch experiment summary when component renders
  const { data: experimentSummary, isLoading: isLoadingSummary } = useExperimentSummary(
    experimentId,
    !!experimentId
  );

  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  const [expandedSchemas, setExpandedSchemas] = useState<Set<number>>(new Set());
  const [savedSchemas, setSavedSchemas] = useState<Set<string>>(new Set());
  const [savingSchemas, setSavingSchemas] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  // Get current review app to check existing schemas
  const { data: manifest } = useAppManifest();
  const reviewApp = manifest?.review_app;

  // Use the new hooks for experiment analysis
  const triggerAnalysisMutation = useTriggerExperimentAnalysis();

  // Start with checking if analysis is already running
  const { data: analysisStatus } = useExperimentAnalysisStatus(
    experimentId,
    true // Always enabled to check status
  );

  // Handle analysis status changes and show appropriate messages
  React.useEffect(() => {
    if (!analysisStatus) return;

    console.log(`[ANALYSIS-STATUS] Status: ${analysisStatus.status}`);

    if (analysisStatus.status === "completed") {
      // Refresh the summary to get new results
      queryClient.invalidateQueries({ queryKey: ["experiment-summary", experimentId] });
      toast.success("Analysis completed successfully!");
    } else if (analysisStatus.status === "failed") {
      toast.error(`Analysis failed: ${analysisStatus.message || "Unknown error"}`);
    }
  }, [analysisStatus, queryClient, experimentId]);

  const toggleIssue = (index: number) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedIssues(newExpanded);
  };

  const toggleSchema = (index: number) => {
    const newExpanded = new Set(expandedSchemas);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSchemas(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="h-4 w-4" />;
      case "high":
        return <AlertCircle className="h-4 w-4" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4" />;
      case "low":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getLabelTypeColor = (labelType: string) => {
    switch (labelType) {
      case "FEEDBACK":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "EXPECTATION":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  if (isLoadingSummary) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32" />
        <Skeleton className="h-24" />
      </div>
    );
  }

  if (!experimentSummary?.has_summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            No Analysis Available
          </CardTitle>
          <CardDescription>
            {experimentSummary?.message ||
              "No analysis found. Click 'Run AI Analysis' to generate comprehensive quality analysis."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={() => triggerAnalysisMutation.mutate({ experimentId })}
            disabled={triggerAnalysisMutation.isPending || analysisStatus?.status === "running"}
            className="gap-2"
          >
            {triggerAnalysisMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting Analysis...
              </>
            ) : analysisStatus?.status === "running" ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analysis Running...
              </>
            ) : (
              <>
                <Brain className="h-4 w-4" />
                Run AI Analysis
              </>
            )}
          </Button>
          {analysisStatus?.message && (
            <p className="mt-2 text-sm text-muted-foreground">
              {analysisStatus.status === "running" || analysisStatus.status === "pending"
                ? "Analysis is in progress. This may take several minutes..."
                : analysisStatus.message}
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  const schemas = experimentSummary?.schemas_with_label_types || [];
  const issues = experimentSummary?.detected_issues || [];
  const metadata = experimentSummary?.metadata || {};

  return (
    <div className="space-y-6">
      {/* Analysis Metadata */}
      {metadata.analysis_timestamp && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Brain className="h-5 w-5" />
                AI Analysis Metadata
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => triggerAnalysisMutation.mutate({ experimentId })}
                disabled={triggerAnalysisMutation.isPending || analysisStatus?.status === "running"}
              >
                {triggerAnalysisMutation.isPending || analysisStatus?.status === "running" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                {triggerAnalysisMutation.isPending
                  ? "Computing..."
                  : analysisStatus?.status === "running"
                    ? "Computing..."
                    : analysisStatus?.status === "pending"
                      ? "Computing..."
                      : "Re-run Analysis"}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Timestamp:</span>
                <p className="font-medium">
                  {new Date(metadata.analysis_timestamp).toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Model:</span>
                <p className="font-medium">{metadata.model_endpoint}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Traces Analyzed:</span>
                <p className="font-medium">{metadata.traces_analyzed || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="report" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="report">Analysis</TabsTrigger>
          <TabsTrigger value="issues" className="gap-2">
            Quality Issues
            {issues.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {issues.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="schemas" className="gap-2">
            Suggested Schemas
            {schemas.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {schemas.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Analysis Report Tab with loading overlay */}
        <TabsContent value="report" className="relative">
          <Card>
            <CardContent className="p-6">
              <Markdown
                content={experimentSummary.content}
                variant="large"
                className="text-foreground"
              />
            </CardContent>
          </Card>
          
          {/* Loading overlay when analysis is running */}
          {(triggerAnalysisMutation.isPending || analysisStatus?.status === "running" || analysisStatus?.status === "pending") && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-lg">
              <div className="flex flex-col items-center space-y-4">
                <div className="relative">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <div className="absolute inset-0 h-8 w-8 rounded-full bg-primary/20 animate-pulse" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-sm font-medium animate-pulse">Computing Analysis...</p>
                  <p className="text-xs text-muted-foreground">This may take several minutes</p>
                </div>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Quality Issues Tab */}
        <TabsContent value="issues">
          <div className="space-y-4">
            {issues.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-muted-foreground">
                  No quality issues detected in this experiment.
                </CardContent>
              </Card>
            ) : (
              issues.map((issue: Issue, index: number) => (
                <Card key={index}>
                  <CardHeader className="cursor-pointer" onClick={() => toggleIssue(index)}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getSeverityIcon(issue.severity)}
                        <div>
                          <CardTitle className="text-lg">{issue.title}</CardTitle>
                          <CardDescription className="mt-1">{issue.description}</CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={getSeverityColor(issue.severity)}>{issue.severity}</Badge>
                        <Badge variant="outline">{issue.affected_traces} traces</Badge>
                        {expandedIssues.has(index) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  {expandedIssues.has(index) && (
                    <CardContent>
                      <div className="space-y-4">
                        {issue.problem_snippets && issue.problem_snippets.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">Problem Examples:</h4>
                            <div className="space-y-2">
                              {issue.problem_snippets.map((snippet, i) => (
                                <Alert key={i}>
                                  <AlertDescription className="font-mono text-sm">
                                    {snippet}
                                  </AlertDescription>
                                </Alert>
                              ))}
                            </div>
                          </div>
                        )}
                        {issue.example_traces && issue.example_traces.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">
                              Affected Traces ({issue.example_traces.length} shown):
                            </h4>
                            <div className="border rounded-lg overflow-hidden">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead className="w-12">#</TableHead>
                                    <TableHead>Trace ID</TableHead>
                                    <TableHead className="w-24">Actions</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {issue.example_traces.map((traceId, i) => (
                                    <TableRow key={i}>
                                      <TableCell className="font-mono text-xs text-muted-foreground">
                                        {i + 1}
                                      </TableCell>
                                      <TableCell className="font-mono text-sm">{traceId}</TableCell>
                                      <TableCell>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="h-7 px-2"
                                          onClick={() => {
                                            // Open trace in new tab
                                            window.open(
                                              `https://eng-ml-inference-team-us-west-2.cloud.databricks.com/ml/experiments/${experimentId}/traces?requestId=${traceId}`,
                                              "_blank"
                                            );
                                          }}
                                        >
                                          <ExternalLink className="h-3 w-3" />
                                        </Button>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                            {issue.affected_traces > issue.example_traces.length && (
                              <p className="text-sm text-muted-foreground mt-2">
                                ... and {issue.affected_traces - issue.example_traces.length} more
                                traces
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* Suggested Schemas Tab */}
        <TabsContent value="schemas">
          <div className="space-y-4">
            {schemas.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center text-muted-foreground">
                  No evaluation schemas recommended.
                </CardContent>
              </Card>
            ) : (
              schemas.map((schema: Schema, index: number) => {
                const isSchemaAlreadySaved =
                  reviewApp?.labeling_schemas?.some(
                    (existingSchema: { name?: string }) => existingSchema.name === schema.key
                  ) || savedSchemas.has(schema.key);
                const isSaving = savingSchemas.has(schema.key);

                // Transform schema to match the format expected by SchemaPreview
                const previewSchema = {
                  ...schema,
                  title: schema.name,
                  instruction: schema.description,
                  enable_comment: true,
                  // Parse numerical schemas
                  ...(schema.schema_type === "numerical" && {
                    min: 1,
                    max: 5,
                  }),
                  // Parse categorical schemas (e.g., pass/fail)
                  ...(schema.schema_type === "categorical" && {
                    options: ["Yes", "No", "Not Applicable"],
                  }),
                  // Parse text schemas
                  ...(schema.schema_type === "text" && {
                    max_length: 500,
                  }),
                };

                const handleSaveSchema = async () => {
                  setSavingSchemas(new Set([...savingSchemas, schema.key]));
                  try {
                    // Transform schema to review app format
                    const newSchema = {
                      name: schema.key,
                      title: schema.name,
                      instruction: schema.description,
                      type: schema.label_type,
                      enable_comment: true,
                      ...(schema.schema_type === "numerical" && {
                        numeric: { min_value: 1, max_value: 5 },
                      }),
                      ...(schema.schema_type === "categorical" && {
                        categorical: { options: ["Yes", "No", "Not Applicable"] },
                      }),
                      ...(schema.schema_type === "text" && {
                        text: { max_length: 500 },
                      }),
                    };

                    // Create new schema via API
                    if (reviewApp?.review_app_id) {
                      await ReviewAppsService.createSchemaApiReviewAppsReviewAppIdSchemasPost(
                        reviewApp.review_app_id,
                        newSchema
                      );

                      setSavedSchemas(new Set([...savedSchemas, schema.key]));
                      toast.success(`Schema "${schema.name}" saved successfully!`);
                      queryClient.invalidateQueries({ queryKey: ["reviewApps"] });
                    }
                  } catch (error) {
                    console.error("Failed to save schema:", error);
                    toast.error(`Failed to save schema: ${error}`);
                  } finally {
                    setSavingSchemas((prev) => {
                      const newSet = new Set(prev);
                      newSet.delete(schema.key);
                      return newSet;
                    });
                  }
                };

                return (
                  <Card key={index}>
                    <CardHeader className="cursor-pointer" onClick={() => toggleSchema(index)}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <ClipboardList className="h-4 w-4" />
                          <div>
                            <CardTitle className="text-lg">{schema.name}</CardTitle>
                            <CardDescription className="mt-1">{schema.description}</CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getLabelTypeColor(schema.label_type)}>
                            {schema.label_type}
                          </Badge>
                          <Badge variant="outline">{schema.schema_type}</Badge>
                          {expandedSchemas.has(index) ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    {expandedSchemas.has(index) && (
                      <CardContent>
                        <div className="space-y-4">
                          {schema.rationale && (
                            <div>
                              <h4 className="font-medium mb-2">Rationale:</h4>
                              <p className="text-sm text-muted-foreground">{schema.rationale}</p>
                            </div>
                          )}

                          {/* SME Preview Section - Always Visible */}
                          <div className="pt-4 border-t">
                            <h4 className="font-medium mb-3">SME Preview</h4>
                            <div className="bg-muted/30 p-4 rounded-lg">
                              <SchemaPreview schema={previewSchema} disabled={false} />
                            </div>
                          </div>

                          <div className="pt-4 border-t flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm">
                              <Tag className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Key:</span>
                              <code className="px-2 py-1 bg-muted rounded">{schema.key}</code>
                            </div>

                            <Button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSaveSchema();
                              }}
                              disabled={
                                isSchemaAlreadySaved || isSaving || !reviewApp?.review_app_id
                              }
                              size="sm"
                            >
                              {isSaving ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Saving...
                                </>
                              ) : isSchemaAlreadySaved ? (
                                <>
                                  <Check className="h-4 w-4 mr-2" />
                                  Saved
                                </>
                              ) : (
                                <>
                                  <Save className="h-4 w-4 mr-2" />
                                  Save Schema
                                </>
                              )}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
