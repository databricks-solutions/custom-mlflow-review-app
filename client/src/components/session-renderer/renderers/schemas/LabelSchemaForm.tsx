import React, { useMemo } from "react";
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
  // Find the first schema that doesn't have a completed assessment
  const defaultValue = useMemo(() => {
    // Helper function to check if a schema is completed
    const isSchemaCompleted = (schema: LabelingSchema): boolean => {
      const assessment = assessments.get(schema.name);
      const value = assessment?.value;
      return value !== undefined && value !== null && value !== "";
    };

    // Find first incomplete schema
    const firstIncomplete = schemas.find(schema => !isSchemaCompleted(schema));
    
    // If there's an incomplete schema, expand it; otherwise collapse all
    return firstIncomplete?.name || "";
  }, [schemas, assessments]);

  return (
    <Accordion type="single" collapsible className="w-full space-y-2" defaultValue={defaultValue}>
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
