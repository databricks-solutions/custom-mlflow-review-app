/**
 * Utilities for combining schemas with their assessments
 */

import { Assessment } from "@/types/assessment";
import { LabelingSchema } from "@/fastapi_client";

export interface SchemaWithAssessment {
  schema: LabelingSchema;
  assessment?: Assessment;
}

/**
 * Combines labeling schemas with their corresponding assessments
 * Returns an array of schemas, each paired with its assessment (if it exists)
 * 
 * @param schemas - Array of labeling schemas
 * @param assessments - Array of assessments (from trace data)
 * @returns Array of schemas with their assessments
 */
export function combineSchemaWithAssessments(
  schemas: LabelingSchema[],
  assessments?: Assessment[]
): SchemaWithAssessment[] {
  // Create a map of assessments by name for O(1) lookup
  const assessmentMap = new Map<string, Assessment>();
  
  if (assessments) {
    // Group assessments by name and pick the most recent one
    assessments.forEach(assessment => {
      const existing = assessmentMap.get(assessment.name);
      
      // If no existing assessment or this one is newer, use it
      if (!existing || 
          (assessment.timestamp && existing.timestamp && 
           new Date(assessment.timestamp) > new Date(existing.timestamp))) {
        assessmentMap.set(assessment.name, assessment);
      } else if (!existing) {
        assessmentMap.set(assessment.name, assessment);
      }
    });
  }
  
  // Combine each schema with its assessment
  return schemas.map(schema => ({
    schema,
    assessment: assessmentMap.get(schema.name)
  }));
}

/**
 * Filters schemas with assessments by type
 * 
 * @param schemasWithAssessments - Combined schemas and assessments
 * @param type - Type to filter by ('FEEDBACK' or 'EXPECTATION')
 * @returns Filtered array
 */
export function filterByType(
  schemasWithAssessments: SchemaWithAssessment[],
  type: 'FEEDBACK' | 'EXPECTATION'
): SchemaWithAssessment[] {
  return schemasWithAssessments.filter(item => item.schema.type === type);
}

/**
 * Checks if a schema has been completed (has a value)
 * 
 * @param schemaWithAssessment - Schema with its assessment
 * @returns True if the schema has a value
 */
export function isSchemaCompleted(schemaWithAssessment: SchemaWithAssessment): boolean {
  const assessment = schemaWithAssessment.assessment;
  return assessment?.value !== undefined && 
         assessment?.value !== null && 
         assessment?.value !== "";
}