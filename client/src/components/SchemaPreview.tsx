import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { JsonValue } from "@/types/renderers";

interface SchemaPreviewProps {
  schema: {
    key: string;
    name: string;
    label_type: "FEEDBACK" | "EXPECTATION" | "NOT_SPECIFIED";
    schema_type: string;
    description: string;
    title?: string;
    instruction?: string;
    min?: number;
    max?: number;
    options?: string[];
    max_length?: number;
    enable_comment?: boolean;
  };
  value?: Record<string, JsonValue>;
  onChange?: (value: Record<string, JsonValue>) => void;
  disabled?: boolean;
}

export const SchemaPreview: React.FC<SchemaPreviewProps> = ({
  schema,
  value = {},
  onChange,
  disabled = false,
}) => {
  const [localValue, setLocalValue] = useState(value[schema.key] || "");
  const [comment, setComment] = useState(value[`${schema.key}_comment`] || "");

  const handleValueChange = (newValue: JsonValue) => {
    setLocalValue(newValue);
    if (onChange) {
      onChange({
        ...value,
        [schema.key]: newValue,
        ...(comment ? { [`${schema.key}_comment`]: comment } : {}),
      });
    }
  };

  const handleCommentChange = (newComment: string) => {
    setComment(newComment);
    if (onChange) {
      onChange({
        ...value,
        [schema.key]: localValue,
        [`${schema.key}_comment`]: newComment,
      });
    }
  };

  // Determine schema input type
  const renderInput = () => {
    if (schema.schema_type === "numerical" || schema.schema_type === "numeric") {
      const min = schema.min ?? 1;
      const max = schema.max ?? 5;
      const currentValue = localValue || min;

      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{min}</span>
            <span className="text-lg font-semibold">{currentValue}</span>
            <span className="text-sm text-muted-foreground">{max}</span>
          </div>
          <Slider
            value={[currentValue]}
            onValueChange={(values) => handleValueChange(values[0])}
            min={min}
            max={max}
            step={1}
            disabled={disabled}
          />
        </div>
      );
    }

    if (schema.schema_type === "categorical" && schema.options) {
      return (
        <RadioGroup value={localValue} onValueChange={handleValueChange} disabled={disabled}>
          {schema.options.map((option) => (
            <div key={option} className="flex items-center space-x-2">
              <RadioGroupItem value={option} id={`${schema.key}-${option}`} />
              <Label htmlFor={`${schema.key}-${option}`}>{option}</Label>
            </div>
          ))}
        </RadioGroup>
      );
    }

    if (schema.schema_type === "text") {
      return (
        <Textarea
          value={localValue}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder="Enter your response..."
          rows={3}
          maxLength={schema.max_length}
          disabled={disabled}
        />
      );
    }

    // Default to text input
    return (
      <Input
        value={localValue}
        onChange={(e) => handleValueChange(e.target.value)}
        placeholder="Enter value..."
        disabled={disabled}
      />
    );
  };

  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardContent className="p-4 space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <h4 className="font-medium text-sm">{schema.title || schema.name}</h4>
            {schema.instruction && (
              <p className="text-sm text-muted-foreground">{schema.instruction}</p>
            )}
            {schema.description && !schema.instruction && (
              <p className="text-sm text-muted-foreground">{schema.description}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Badge
              variant={
                schema.label_type === "FEEDBACK"
                  ? "default"
                  : schema.label_type === "EXPECTATION"
                    ? "secondary"
                    : "outline"
              }
            >
              {schema.label_type}
            </Badge>
          </div>
        </div>

        {renderInput()}

        {schema.enable_comment !== false && (
          <div className="space-y-2 pt-2 border-t">
            <Label htmlFor={`${schema.key}_comment`}>Comments (Optional)</Label>
            <Textarea
              id={`${schema.key}_comment`}
              value={comment}
              onChange={(e) => handleCommentChange(e.target.value)}
              placeholder="Add your reasoning or additional context..."
              rows={2}
              disabled={disabled}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
};
