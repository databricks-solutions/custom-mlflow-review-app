import React, { useState, useEffect } from "react";
import { Accordion } from "@/components/ui/accordion";
import { Assessment, LabelingSchema } from "@/types/renderers";
import { LabelSchemaField } from "./LabelSchemaField";

interface LabelSchemaFormProps {
  schemas: LabelingSchema[];
  assessments: Map<string, Assessment>;
  traceId: string;
  readOnly?: boolean;
  reviewAppId?: string;
  sessionId?: string;
}

export function LabelSchemaForm({
  schemas,
  assessments,
  traceId,
  readOnly = false,
  reviewAppId,
  sessionId,
}: LabelSchemaFormProps) {
  // State to control which accordion item is open
  const [expandedValue, setExpandedValue] = useState<string>("");
  // Track if we've initialized the accordion state for this trace
  const [hasInitialized, setHasInitialized] = useState(false);
  // Track the current trace ID to detect when it changes
  const [currentTraceId, setCurrentTraceId] = useState(traceId);

  // Detect when we navigate to a new trace
  const isNewTrace = currentTraceId !== traceId;
  
  // When trace changes, reset initialization flag
  useEffect(() => {
    if (isNewTrace) {
      setCurrentTraceId(traceId);
      setHasInitialized(false);
    }
  }, [traceId, isNewTrace]);

  // Set initial accordion state only when trace changes or on first load
  useEffect(() => {
    // Only set initial state if we haven't initialized yet
    if (!hasInitialized) {
      // Helper function to check if a schema is completed
      const isSchemaCompleted = (schema: LabelingSchema): boolean => {
        const assessment = assessments.get(schema.name);
        const value = assessment?.value;
        // More thorough check for completed assessments
        if (value === undefined || value === null || value === "") {
          return false;
        }
        // For arrays, check if they have length
        if (Array.isArray(value) && value.length === 0) {
          return false;
        }
        // For objects, check if they have meaningful content
        if (typeof value === "object" && Object.keys(value).length === 0) {
          return false;
        }
        return true;
      };

      // Find first incomplete schema
      const firstIncomplete = schemas.find(schema => !isSchemaCompleted(schema));
      
      // If there's an incomplete schema, expand it; otherwise collapse all (empty string)
      const targetValue = firstIncomplete?.name || "";
      
      setExpandedValue(targetValue);
      setHasInitialized(true);
    }
  }, [hasInitialized, schemas, assessments, traceId]);

  return (
    <Accordion 
      type="single" 
      collapsible 
      className="w-full space-y-2" 
      value={expandedValue}
      onValueChange={setExpandedValue}
    >
      {schemas.map((schema) => (
        <LabelSchemaField
          key={`${schema.name}-${traceId}`}
          schema={schema}
          assessment={assessments.get(schema.name)}
          traceId={traceId}
          readOnly={readOnly}
          reviewAppId={reviewAppId}
          sessionId={sessionId}
        />
      ))}
    </Accordion>
  );
}
