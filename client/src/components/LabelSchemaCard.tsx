import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { LabelingSchema } from "@/fastapi_client";

interface LabelSchemaCardProps {
  schema: LabelingSchema;
  originalSchemaName: string;
  onSchemaChange: (updatedSchema: LabelingSchema, originalSchemaName: string) => void;
  onSave?: (schema: LabelingSchema) => void;
  onDelete?: (schema: LabelingSchema) => void;
  isSaving?: boolean;
  isDeleting?: boolean;
}

export function LabelSchemaCard({
  schema,
  originalSchemaName,
  onSchemaChange,
  onSave,
  onDelete,
  isSaving = false,
  isDeleting = false,
}: LabelSchemaCardProps) {
  const updateSchema = (updates: Partial<LabelingSchema>) => {
    const updatedSchema = { ...schema, ...updates };
    onSchemaChange(updatedSchema, originalSchemaName);
  };

  const handleSave = () => {
    if (onSave) {
      onSave(schema);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(schema);
    }
  };

  const getSchemaType = () => {
    if (schema.categorical) {
      const options = schema.categorical.options || [];
      if (options.length === 2) {
        const lowerOptions = options.map((opt) => opt.toLowerCase());
        if (lowerOptions.includes("yes") && lowerOptions.includes("no")) {
          return "pass_fail";
        }
      }
      return "categorical";
    }
    if (schema.categorical_list) return "categorical_list";
    if (schema.text) return "text";
    if (schema.text_list) return "text_list";
    if (schema.numeric) return "numeric";
    return "text";
  };

  const changeSchemaType = (newType: string) => {
    const newSchema: Partial<LabelingSchema> = {
      ...schema,
    };

    // Clear existing schema fields
    newSchema.categorical = undefined;
    newSchema.categorical_list = undefined;
    newSchema.text = undefined;
    newSchema.text_list = undefined;
    newSchema.numeric = undefined;

    // Set defaults based on type
    if (newType === "text") {
      newSchema.text = { max_length: 500 };
    } else if (newType === "text_list") {
      newSchema.text_list = { max_length_each: 500, max_count: 5 };
    } else if (newType === "categorical") {
      newSchema.categorical = { options: ["Option 1", "Option 2"] };
    } else if (newType === "categorical_list") {
      newSchema.categorical_list = { options: ["Option 1", "Option 2"] };
    } else if (newType === "numeric") {
      newSchema.numeric = { min_value: 0, max_value: 10 };
    } else if (newType === "pass_fail") {
      newSchema.categorical = { options: ["Yes", "No"] };
    }

    updateSchema(newSchema);
  };

  const renderTypeSpecificEditor = () => {
    const currentType = getSchemaType();

    if (currentType === "pass_fail") {
      return null; // Pass/Fail has fixed options
    }

    if (currentType === "categorical" || currentType === "categorical_list") {
      const options =
        currentType === "categorical"
          ? schema.categorical?.options || []
          : schema.categorical_list?.options || [];

      const updateOptions = (newOptions: string[]) => {
        if (currentType === "categorical") {
          updateSchema({ categorical: { options: newOptions } });
        } else {
          updateSchema({ categorical_list: { options: newOptions } });
        }
      };

      const addOption = () => {
        updateOptions([...options, `Option ${options.length + 1}`]);
      };

      const removeOption = (index: number) => {
        const newOptions = [...options];
        newOptions.splice(index, 1);
        updateOptions(newOptions);
      };

      const updateOption = (index: number, value: string) => {
        const newOptions = [...options];
        newOptions[index] = value;
        updateOptions(newOptions);
      };

      return (
        <div className="space-y-3">
          <Label>Options</Label>
          <div className="space-y-2">
            {options.map((option, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={option}
                  onChange={(e) => updateOption(index, e.target.value)}
                  placeholder={`Option ${index + 1}`}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeOption(index)}
                  disabled={options.length <= 1}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addOption}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Option
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Configure the {currentType === "categorical" ? "single-select" : "multi-select"} options
            that users can choose from
          </p>
        </div>
      );
    }

    if (currentType === "text") {
      return (
        <div className="space-y-3">
          <Label>Text Settings</Label>
          <div className="flex gap-4 items-center">
            <Label className="text-sm font-normal">Max Length:</Label>
            <Input
              type="number"
              value={schema.text?.max_length?.toString() || ""}
              onChange={(e) => {
                const value = e.target.value ? parseInt(e.target.value) : undefined;
                updateSchema({ text: { max_length: value ?? undefined } });
              }}
              placeholder="No limit"
              className="w-32"
            />
          </div>
          <p className="text-sm text-muted-foreground">
            Set a character limit for text input, or leave empty for no limit
          </p>
        </div>
      );
    }

    if (currentType === "text_list") {
      return (
        <div className="space-y-3">
          <Label>Text List Settings</Label>
          <div className="flex gap-4 items-center">
            <div className="flex gap-2 items-center">
              <Label className="text-sm font-normal whitespace-nowrap">Max Length Each:</Label>
              <Input
                type="number"
                value={schema.text_list?.max_length_each?.toString() || ""}
                onChange={(e) => {
                  const value = e.target.value ? parseInt(e.target.value) : undefined;
                  updateSchema({ text_list: { ...schema.text_list, max_length_each: value } });
                }}
                placeholder="No limit"
                className="w-24"
              />
            </div>
            <div className="flex gap-2 items-center">
              <Label className="text-sm font-normal whitespace-nowrap">Max Count:</Label>
              <Input
                type="number"
                value={schema.text_list?.max_count?.toString() || ""}
                onChange={(e) => {
                  const value = e.target.value ? parseInt(e.target.value) : undefined;
                  updateSchema({ text_list: { ...schema.text_list, max_count: value } });
                }}
                placeholder="No limit"
                className="w-24"
              />
            </div>
          </div>
        </div>
      );
    }

    if (currentType === "numeric") {
      return (
        <div className="space-y-3">
          <Label>Numeric Settings</Label>
          <div className="space-y-2">
            <div className="flex gap-4 items-center">
              <Label className="text-sm font-normal min-w-[80px]">Min Value:</Label>
              <Input
                type="number"
                value={schema.numeric?.min_value?.toString() || ""}
                onChange={(e) => {
                  const value = e.target.value ? parseFloat(e.target.value) : undefined;
                  updateSchema({ numeric: { ...schema.numeric, min_value: value ?? undefined } });
                }}
                placeholder="No minimum"
                className="w-32"
              />
            </div>
            <div className="flex gap-4 items-center">
              <Label className="text-sm font-normal min-w-[80px]">Max Value:</Label>
              <Input
                type="number"
                value={schema.numeric?.max_value?.toString() || ""}
                onChange={(e) => {
                  const value = e.target.value ? parseFloat(e.target.value) : undefined;
                  updateSchema({ numeric: { ...schema.numeric, max_value: value ?? undefined } });
                }}
                placeholder="No maximum"
                className="w-32"
              />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Define the acceptable range for numeric input values
          </p>
        </div>
      );
    }

    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Schema Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Schema name and type row */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="assessment-name">Assessment name</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>
                      A unique identifier for this assessment. Used internally to reference this
                      task.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Input
              id="assessment-name"
              value={schema.name || ""}
              onChange={(e) => updateSchema({ name: e.target.value })}
              placeholder="unique_assessment_key"
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="assessment-type">Assessment type</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>
                      Choose whether this task collects feedback or expectations from reviewers.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Select
              value={schema.type || "FEEDBACK"}
              onValueChange={(value: "FEEDBACK" | "EXPECTATION") => updateSchema({ type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="EXPECTATION">Expectation</SelectItem>
                <SelectItem value="FEEDBACK">Feedback</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Title field */}
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={schema.title || ""}
            onChange={(e) => updateSchema({ title: e.target.value })}
            placeholder="Title shown to reviewers for this task"
          />
          <p className="text-sm text-muted-foreground">
            The title displayed to reviewers when completing this assessment
          </p>
        </div>

        {/* Instructions field */}
        <div className="space-y-2">
          <Label htmlFor="instruction">Instructions</Label>
          <Textarea
            id="instruction"
            value={schema.instruction || ""}
            onChange={(e) => updateSchema({ instruction: e.target.value })}
            placeholder="Instructions for reviewers on how to complete this task"
            rows={3}
          />
        </div>

        {/* Input type */}
        <div className="space-y-2">
          <Label>Input type</Label>
          <Select value={getSchemaType()} onValueChange={changeSchemaType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pass_fail">Pass/Fail</SelectItem>
              <SelectItem value="categorical">Categorical (Single Choice)</SelectItem>
              <SelectItem value="categorical_list">Categorical List (Multiple Choice)</SelectItem>
              <SelectItem value="text">Text</SelectItem>
              <SelectItem value="text_list">Text List</SelectItem>
              <SelectItem value="numeric">Numeric</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Enable comments */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="enable-comment"
            checked={schema.enable_comment || false}
            onCheckedChange={(checked) => updateSchema({ enable_comment: !!checked })}
          />
          <Label htmlFor="enable-comment">Enable comments</Label>
          <p className="text-sm text-muted-foreground ml-2">
            Allow users to add additional comments alongside their assessment
          </p>
        </div>

        {/* Type-specific editor */}
        {renderTypeSpecificEditor()}

        {/* Action buttons */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          {onDelete && (
            <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          )}
          {onSave && (
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
