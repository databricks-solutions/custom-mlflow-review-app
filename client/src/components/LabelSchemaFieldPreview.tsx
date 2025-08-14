import React from "react";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { LabelingSchema } from "@/types/renderers";

interface LabelSchemaFieldPreviewProps {
  schema: LabelingSchema;
}

export function LabelSchemaFieldPreview({ schema }: LabelSchemaFieldPreviewProps) {
  // Default values for preview
  const defaultNumericValue = schema.numeric 
    ? Math.floor((schema.numeric.min_value + schema.numeric.max_value) / 2)
    : 0;

  return (
    <AccordionItem value={schema.name} className="border rounded-lg px-4">
      <AccordionTrigger className="hover:no-underline">
        <span className="font-medium">{schema.title || schema.name}</span>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pt-4">
        {schema.instruction && (
          <p className="text-sm text-muted-foreground">{schema.instruction}</p>
        )}

        {/* Numeric rating */}
        {schema.numeric && (
          <div className="space-y-2">
            <Label>Rating</Label>
            <Slider
              value={[defaultNumericValue]}
              min={schema.numeric.min_value}
              max={schema.numeric.max_value}
              step={1}
              disabled={true}
              className="py-4 opacity-60"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{schema.numeric.min_value}</span>
              <span className="font-medium text-foreground">
                {defaultNumericValue}
              </span>
              <span>{schema.numeric.max_value}</span>
            </div>
          </div>
        )}

        {/* Categorical options */}
        {schema.categorical && (
          <RadioGroup disabled={true} className="opacity-60">
            {schema.categorical.options?.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <RadioGroupItem value={option} id={`preview-${schema.name}-${option}`} />
                <Label htmlFor={`preview-${schema.name}-${option}`}>{option}</Label>
              </div>
            ))}
          </RadioGroup>
        )}

        {/* Text input */}
        {schema.text && (
          <div className="space-y-2">
            <Label htmlFor={`preview-${schema.name}`}>Response</Label>
            <Textarea
              id={`preview-${schema.name}`}
              placeholder="Enter your response..."
              rows={4}
              disabled={true}
              className="opacity-60"
            />
          </div>
        )}

        {/* Rationale/Comments */}
        {schema.enable_comment && (
          <div className="space-y-2 pt-2 border-t">
            <Label htmlFor={`preview-${schema.name}_rationale`}>Comments</Label>
            <Textarea
              id={`preview-${schema.name}_rationale`}
              placeholder="Add your reasoning or additional feedback..."
              rows={2}
              disabled={true}
              className="opacity-60"
            />
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}