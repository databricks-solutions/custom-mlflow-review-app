import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Plus, Trash2, Save, Info, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ReviewAppsService } from "@/fastapi_client";
import { LabelingSchema } from "@/types/renderers";
import {
  useConfig,
  useAppManifest,
  useLabelingSessions,
  useLabelSchemas,
  useCreateLabelSchema,
  useUpdateLabelSchema,
  useDeleteLabelSchema,
  useUserRole,
} from "@/hooks/api-hooks";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export function LabelingSchemasPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Get user role to determine if dev navigation should be shown
  const { data: userRole } = useUserRole();

  // Get labeling sessions for usage tracking
  const { data: sessionsData, isLoading: isLoadingSessions } = useLabelingSessions();

  // Get schemas from API
  const { data: schemas = [], isLoading: isLoadingSchemas } = useLabelSchemas();

  // Schema mutations
  const createSchemaMutation = useCreateLabelSchema();
  const updateSchemaMutation = useUpdateLabelSchema();
  const deleteSchemaMutation = useDeleteLabelSchema();

  // Schema editing state
  const [editingSchemas, setEditingSchemas] = useState<Record<string, Partial<LabelingSchema>>>({});
  const [savingSchemas, setSavingSchemas] = useState<Set<string>>(new Set());
  const [deletingSchemas, setDeletingSchemas] = useState<Set<string>>(new Set());
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<string | null>(null);
  const [newlyCreatedSchemas, setNewlyCreatedSchemas] = useState<Set<string>>(new Set());

  const isLoading = isLoadingSessions || isLoadingSchemas;

  // Schema editing functions
  const initializeSchemaForEditing = (schema: LabelingSchema) => {
    if (!editingSchemas[schema.name]) {
      setEditingSchemas((prev) => ({
        ...prev,
        [schema.name]: { ...schema },
      }));
    }
  };

  const updateEditingSchema = (schemaName: string, updates: Partial<LabelingSchema>) => {
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

  const getSchemaType = (schema: LabelingSchema) => {
    if (schema.categorical) {
      const options = schema.categorical.options || [];
      if (options.length === 2) {
        // Check for boolean-like options (case-insensitive)
        const lowerOptions = options.map((opt: string) => opt.toLowerCase());
        if (
          (lowerOptions.includes("true") && lowerOptions.includes("false")) ||
          (lowerOptions.includes("yes") && lowerOptions.includes("no")) ||
          (lowerOptions.includes("pass") && lowerOptions.includes("fail"))
        ) {
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
    const newSchema: Partial<LabelingSchema> = { ...editingSchemas[schemaName] };

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
      newSchema.categorical = { options: ["yes", "no"] };
    }

    setEditingSchemas((prev) => ({
      ...prev,
      [schemaName]: newSchema,
    }));
  };

  const handleSaveSchema = async (schemaName: string) => {
    setSavingSchemas((prev) => new Set([...prev, schemaName]));
    try {
      await updateSchemaMutation.mutateAsync({
        schemaName: schemaName,
        schema: editingSchemas[schemaName],
      });
      
      // Clear the editing state for this schema once saved
      setEditingSchemas((prev) => {
        const updated = { ...prev };
        delete updated[schemaName];
        return updated;
      });
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
      await deleteSchemaMutation.mutateAsync({
        schemaName: schemaName,
      });

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

  const handleCreateSchema = async () => {
    // Generate unique name for new schema
    let schemaName = "new_assessment";
    let counter = 1;

    // Find unique name by appending counter if needed
    while (schemas.find((s) => s.name === schemaName)) {
      counter++;
      schemaName = `new_assessment_${counter}`;
    }

    // Create new pass/fail schema with unique name
    const newSchema = {
      name: schemaName,
      title: `Assessment ${counter > 1 ? counter : ""}`.trim(),
      instruction: "Rate this interaction",
      type: "FEEDBACK",
      categorical: {
        options: ["yes", "no"],
      },
      enable_comment: true,
    };

    try {
      await createSchemaMutation.mutateAsync(newSchema);

      // Track as newly created so it appears first
      setNewlyCreatedSchemas((prev) => new Set([...prev, schemaName]));
      
      toast.success(`Created new assessment schema: ${schemaName}`);
    } catch (error) {
      toast.error("Failed to create schema");
      console.error(error);
    }
  };

  if (isLoading) {
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
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Label Schemas</h1>
            <p className="text-muted-foreground mt-2">
              Configure your label schemas to set how the labels will be collected and how questions
              will be asked to your subject matter experts.
            </p>
          </div>
          <Button 
            onClick={handleCreateSchema}
            disabled={createSchemaMutation.isPending}
          >
            <Plus className="h-4 w-4 mr-2" />
            {createSchemaMutation.isPending ? "Creating..." : "Create Schema"}
          </Button>
        </div>
      </div>

      {/* Schema List */}
      {schemas && schemas.length > 0 ? (
        <div className="space-y-6">
          {[...schemas]
            .sort((a, b) => {
              // Put newly created schemas first
              const aIsNew = newlyCreatedSchemas.has(a.name);
              const bIsNew = newlyCreatedSchemas.has(b.name);
              if (aIsNew && !bIsNew) return -1;
              if (!aIsNew && bIsNew) return 1;
              // Otherwise sort alphabetically
              return (a.title || a.name).localeCompare(b.title || b.name);
            })
            .map((schema) => {
              // Initialize editing state for this schema
              initializeSchemaForEditing(schema);
              const editingSchema = editingSchemas[schema.name] || schema;
              const currentType = getSchemaType(editingSchema);
              const isSaving = savingSchemas.has(schema.name);
              const isDeleting = deletingSchemas.has(schema.name);
              const usageCount = getSchemaUsageCount(schema.name);

              return (
                <Card
                  key={schema.name}
                  className="border shadow-sm transition-all duration-300"
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
                          <SelectItem value="categorical">
                            Categorical (Single Choice)
                          </SelectItem>
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
                              const value = e.target.value
                                ? parseInt(e.target.value)
                                : undefined;
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialog !== null} onOpenChange={() => setDeleteConfirmDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Label Schema</DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-2">
                <div>
                  Are you sure you want to delete the schema "{deleteConfirmDialog}"? This action
                  cannot be undone.
                </div>
                {deleteConfirmDialog && (
                  <div className="bg-muted/50 rounded-lg p-3 mt-3">
                    <div className="text-sm font-medium mb-1">Usage Information:</div>
                    {getSchemaUsageCount(deleteConfirmDialog) === 0 ? (
                      <div className="text-sm text-muted-foreground">
                        This schema is not currently used by any labeling sessions.
                      </div>
                    ) : (
                      <div className="text-sm">
                        <div className="text-orange-600 font-medium">
                          ⚠️ This schema is currently used by{" "}
                          {getSchemaUsageCount(deleteConfirmDialog)} labeling session
                          {getSchemaUsageCount(deleteConfirmDialog) > 1 ? "s" : ""}:
                        </div>
                        <ul className="list-disc list-inside mt-1 text-muted-foreground">
                          {getSessionsUsingSchema(deleteConfirmDialog).map((sessionName, idx) => (
                            <li key={idx}>{sessionName}</li>
                          ))}
                        </ul>
                        <div className="text-sm text-muted-foreground mt-2">
                          Deleting this schema may affect these sessions' evaluation criteria.
                        </div>
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
    </div>
  );
}