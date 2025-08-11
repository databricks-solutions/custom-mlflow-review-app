import React, { useMemo, useState, useEffect } from "react";
import { Accordion } from "@/components/ui/accordion";
import { Assessment, LabelingSchema } from "@/types/renderers";
import { LabelSchemaField } from "./LabelSchemaField";

interface LabelSchemaFormProps {
  schemas: LabelingSchema[];
  assessments: Map<string, Assessment>;
  traceId: string;
  readOnly?: boolean;
}

export function LabelSchemaForm({
  schemas,
  assessments,
  traceId,
  readOnly = false,
}: LabelSchemaFormProps) {
  // State to control which accordion item is open
  const [expandedValue, setExpandedValue] = useState<string>("");

  // Find the first schema that doesn't have a completed assessment
  const targetExpandedValue = useMemo(() => {
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
    
    // Debug logging to understand the behavior
    console.log("[EXPANSION DEBUG]", {
      schemas: schemas.map(s => ({ name: s.name, completed: isSchemaCompleted(s) })),
      firstIncomplete: firstIncomplete?.name,
      willExpand: firstIncomplete?.name || "",
    });
    
    // If there's an incomplete schema, expand it; otherwise collapse all (empty string)
    return firstIncomplete?.name || "";
  }, [schemas, assessments]);

  // Update the expanded value when the target changes
  useEffect(() => {
    setExpandedValue(targetExpandedValue);
  }, [targetExpandedValue]);

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
          key={schema.name}
          schema={schema}
          assessment={assessments.get(schema.name)}
          traceId={traceId}
          readOnly={readOnly}
        />
      ))}
    </Accordion>
  );
}
