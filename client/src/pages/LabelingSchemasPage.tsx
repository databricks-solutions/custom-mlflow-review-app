import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LabelSchemaCard } from "@/components/LabelSchemaCard";
import { useConfig, useReviewApps, useUserRole } from "@/hooks/api-hooks";

// Import the LabelingSchema type from our existing models
import type { LabelingSchema } from "@/fastapi_client";

const LoadingSkeleton = () => {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <Skeleton className="h-12 w-64" />
      <div className="grid gap-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-32" />
      </div>
    </div>
  );
};

export function LabelingSchemasPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // State for delete confirmation and local schema changes
  const [schemaToDelete, setSchemaToDelete] = useState<LabelingSchema | null>(null);
  const [localSchemaChanges, setLocalSchemaChanges] = useState<Map<string, LabelingSchema>>(
    new Map()
  );

  // Get configuration to determine the experiment and review app
  const { data: config, isLoading: isLoadingConfig } = useConfig();

  // Get user role to determine if dev navigation should be shown
  const { data: userRole } = useUserRole();

  // Get review app details based on experiment
  const { data: reviewApps, isLoading: isLoadingReviewApp } = useReviewApps(
    config?.experiment_id ? `experiment_id=${config.experiment_id}` : undefined
  );

  const reviewApp = reviewApps?.review_apps?.[0];

  // TODO: Replace with actual API calls when backend is implemented
  const schemas: LabelingSchema[] = [
    {
      name: "quality_rating",
      title: "Response Quality",
      instruction: "Rate the overall quality of the AI response",
      type: "FEEDBACK",
      enable_comment: true,
      numeric: {
        min_value: 1,
        max_value: 5,
      },
    },
    {
      name: "helpfulness",
      title: "Helpfulness",
      instruction: "How helpful was this response to the user?",
      type: "FEEDBACK",
      enable_comment: false,
      categorical: {
        options: ["Very Helpful", "Somewhat Helpful", "Not Helpful"],
      },
    },
  ];

  const isLoading = isLoadingConfig || isLoadingReviewApp;

  const handleAddSchema = async () => {
    // Generate a unique name for the new schema
    const existingNames = schemas.map((s) => s.name).filter(Boolean);
    let newName = "guidelines";
    let counter = 1;
    while (existingNames.includes(newName)) {
      newName = `guidelines_${counter}`;
      counter++;
    }

    // TODO: Implement actual creation when backend is ready
    console.log("Creating new schema:", newName);
  };

  const handleSaveSchema = async (
    originalSchema: LabelingSchema,
    updatedSchema: LabelingSchema
  ) => {
    if (!originalSchema.name) return;

    try {
      // TODO: Implement actual save when backend is ready
      console.log("Saving schema:", originalSchema.name, updatedSchema);

      // Clear the local changes for this schema once saved
      if (originalSchema.name) {
        setLocalSchemaChanges((prev) => {
          const newMap = new Map(prev);
          newMap.delete(originalSchema.name as string);
          return newMap;
        });
      }
    } catch (error) {
      console.error("Error saving schema:", error);
    }
  };

  const handleDeleteSchema = async (schema: LabelingSchema) => {
    if (!schema.name) return;
    setSchemaToDelete(schema);
  };

  const handleConfirmDelete = async () => {
    if (!schemaToDelete) return;

    try {
      // TODO: Implement actual deletion when backend is ready
      console.log("Deleting schema:", schemaToDelete.name);

      // Clear any local changes for the deleted schema
      if (schemaToDelete.name) {
        setLocalSchemaChanges((prev) => {
          const newMap = new Map(prev);
          newMap.delete(schemaToDelete.name as string);
          return newMap;
        });
      }
      setSchemaToDelete(null);
    } catch (error) {
      console.error("Error deleting schema:", error);
      setSchemaToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setSchemaToDelete(null);
  };

  // Track local schema changes for real-time preview updates
  const handleSchemaChange = (updatedSchema: LabelingSchema, originalSchemaName: string) => {
    setLocalSchemaChanges((prev) => {
      const newMap = new Map(prev);
      newMap.set(originalSchemaName, updatedSchema);
      return newMap;
    });
  };

  // Helper function to get the current schema (local changes or server data)
  const getCurrentSchema = (originalSchema: LabelingSchema): LabelingSchema => {
    if (!originalSchema.name) return originalSchema;
    return localSchemaChanges.get(originalSchema.name) || originalSchema;
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!reviewApp) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No review app found for this experiment. Please create a review app first.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6 h-screen overflow-auto">
      {/* Header */}
      <div className="space-y-4">
        {userRole?.is_developer && (
          <Button variant="ghost" size="sm" onClick={() => navigate("/dev")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        )}

        <div>
          <h1 className="text-3xl font-bold">Label Schemas</h1>
          <p className="text-muted-foreground mt-2">
            Configure your label schemas to set how the labels will be collected and how questions
            will be asked to your subject matter experts.
          </p>
          <Button className="mt-4" onClick={handleAddSchema}>
            <Plus className="h-4 w-4 mr-2" />
            Add Label Schema
          </Button>
        </div>
      </div>

      {/* Schema List - Two Panel Layout */}
      <div className="space-y-6">
        {schemas.map((schema) => {
          if (!schema.name) return null;

          return (
            <div key={schema.name} className="flex gap-6 items-start">
              {/* Left Panel - Schema Editor (65% width) */}
              <div className="flex-[0_0_65%] max-w-[840px]">
                <LabelSchemaCard
                  schema={getCurrentSchema(schema)}
                  originalSchemaName={schema.name}
                  onSchemaChange={handleSchemaChange}
                  onSave={(updatedSchema) => handleSaveSchema(schema, updatedSchema)}
                  onDelete={handleDeleteSchema}
                />
              </div>

              {/* Right Panel - Preview (30% width) */}
              <div className="flex-[0_0_30%]">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Preview</CardTitle>
                    <CardDescription>How this will appear to reviewers</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-green-600 mb-2">
                          ● {getCurrentSchema(schema).title}
                        </h4>
                        {getCurrentSchema(schema).instruction && (
                          <p className="text-sm text-muted-foreground mb-3">
                            {getCurrentSchema(schema).instruction}
                          </p>
                        )}
                      </div>

                      {/* Preview based on schema type */}
                      {getCurrentSchema(schema).categorical && (
                        <div className="space-y-2">
                          {getCurrentSchema(schema).categorical?.options?.map((option, index) => (
                            <label key={index} className="flex items-center space-x-2">
                              <input type="radio" name={`preview-${schema.name}`} disabled />
                              <span className="text-sm">{option}</span>
                            </label>
                          ))}
                        </div>
                      )}

                      {getCurrentSchema(schema).numeric && (
                        <div>
                          <input
                            type="number"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            placeholder="Enter a number..."
                            min={getCurrentSchema(schema).numeric?.min_value}
                            max={getCurrentSchema(schema).numeric?.max_value}
                            disabled
                          />
                          <div className="text-xs text-muted-foreground mt-1">
                            Valid range: {getCurrentSchema(schema).numeric?.min_value} -{" "}
                            {getCurrentSchema(schema).numeric?.max_value}
                          </div>
                        </div>
                      )}

                      {getCurrentSchema(schema).text && (
                        <div>
                          <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            placeholder="Enter your response..."
                            rows={3}
                            disabled
                          />
                          {getCurrentSchema(schema).text?.max_length && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Maximum {getCurrentSchema(schema).text.max_length} characters
                            </div>
                          )}
                        </div>
                      )}

                      {getCurrentSchema(schema).enable_comment && (
                        <div className="pt-3 border-t">
                          <label className="block text-sm font-medium mb-2">Comments</label>
                          <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            placeholder="Additional comments..."
                            rows={2}
                            disabled
                          />
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          );
        })}
      </div>

      {/* Delete Confirmation Dialog */}
      {schemaToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Delete Label Schema</CardTitle>
              <CardDescription>
                Are you sure you want to delete the label schema{" "}
                <strong>{schemaToDelete.name}</strong>? This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={handleCancelDelete}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleConfirmDelete}>
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
