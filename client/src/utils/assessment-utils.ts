/**
 * Utilities for working with assessments and label schemas
 */

import { Assessment } from "@/types/assessment";
import { LabelingSchema } from "@/fastapi_client";

/**
 * Align a label schema with an existing assessment
 * Returns the matching assessment if found, null otherwise
 * 
 * @param schema - The labeling schema to match
 * @param assessments - Array of existing assessments
 * @param currentUser - Current user's email
 * @returns Matching assessment or null
 */
export function alignSchemaToAssessment(
  schema: LabelingSchema,
  assessments: Assessment[] | undefined,
  currentUser: string | undefined
): Assessment | null {
  if (!assessments || assessments.length === 0) {
    return null;
  }

  // Find matching assessment by schema name
  const matchingAssessment = assessments.find((assessment) => {
    // Match by name/key
    if (assessment.name !== schema.name) {
      return false;
    }

    // If current user is defined, prioritize their assessments
    if (currentUser && assessment.user === currentUser) {
      return true;
    }

    // Otherwise, return any matching assessment
    return true;
  });

  return matchingAssessment || null;
}

/**
 * Find the most recent assessment for a schema from a specific user
 */
export function findUserAssessment(
  schema: LabelingSchema,
  assessments: Assessment[] | undefined,
  userEmail: string
): Assessment | null {
  if (!assessments) return null;

  const userAssessments = assessments.filter(
    a => a.name === schema.name && a.user === userEmail
  );

  if (userAssessments.length === 0) return null;

  // Return the most recent assessment
  return userAssessments.reduce((latest, current) => {
    const latestTime = latest.timestamp ? new Date(latest.timestamp).getTime() : 0;
    const currentTime = current.timestamp ? new Date(current.timestamp).getTime() : 0;
    return currentTime > latestTime ? current : latest;
  });
}