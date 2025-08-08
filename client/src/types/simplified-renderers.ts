/**
 * Simplified renderer types for better separation of concerns
 * Renderers should ONLY display content, not handle navigation
 */

import { Assessment } from "@/types/assessment";
import { LabelingSchema } from "@/fastapi_client/models/LabelingSchema";

export interface SimplifiedRendererProps {
  // Core data (read-only)
  item: {
    item_id: string;
    state: string;
    source?: {
      trace_id: string;
    };
  };
  
  traceData: {
    info: {
      trace_id: string;
      request_time: string;
      execution_duration?: string;
      assessments?: Assessment[];
    };
    spans: any[];
  };
  
  reviewApp: {
    review_app_id: string;
    labeling_schemas: LabelingSchema[];
  };
  
  // Assessment state
  assessments: Map<string, Assessment>;
  onAssessmentsChange: (assessments: Map<string, Assessment>) => void;
  
  // Optional: Loading state
  isLoading?: boolean;
}

/**
 * Example simplified renderer
 */
export const ExampleSimplifiedRenderer: React.FC<SimplifiedRendererProps> = ({
  traceData,
  reviewApp,
  assessments,
  onAssessmentsChange,
}) => {
  // Extract conversation
  const { userRequest, assistantResponse } = extractConversation(traceData.spans);
  
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Conversation */}
      <div>
        {userRequest && <ConversationMessage role="user" content={userRequest.content} />}
        {assistantResponse && <ConversationMessage role="assistant" content={assistantResponse.content} />}
      </div>
      
      {/* Right: Assessments */}
      <div>
        <LabelSchemaForm
          schemas={reviewApp.labeling_schemas}
          assessments={assessments}
          onAssessmentSave={(assessment) => {
            const newAssessments = new Map(assessments);
            newAssessments.set(assessment.name, assessment);
            onAssessmentsChange(newAssessments);
          }}
        />
      </div>
    </div>
  );
};