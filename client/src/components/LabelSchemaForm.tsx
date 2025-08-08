import React from "react";
import { Accordion } from "@/components/ui/accordion";
import { Assessment, LabelingSchema } from "@/types/renderers";
import { LabelSchemaField } from "./LabelSchemaField";

interface LabelSchemaFormProps {
  schemas: LabelingSchema[];
  assessments: Map<string, Assessment>;
  onAssessmentSave: (assessment: Assessment) => void;
  readOnly?: boolean;
}

export function LabelSchemaForm({
  schemas,
  assessments,
  onAssessmentSave,
  readOnly = false,
}: LabelSchemaFormProps) {

  return (
    <Accordion type="single" collapsible className="w-full space-y-2">
      {schemas.map((schema) => (
        <LabelSchemaField
          key={schema.name}
          schema={schema}
          assessment={assessments.get(schema.name)}
          onSave={onAssessmentSave}
          readOnly={readOnly}
        />
      ))}
    </Accordion>
  );
}