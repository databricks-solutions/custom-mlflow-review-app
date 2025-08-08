import React, { useCallback, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Wrench,
  User,
  Bot,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { ItemRendererProps, Assessment } from "@/types/renderers";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { useMutation } from "@tanstack/react-query";
import { MLflowService } from "@/fastapi_client";
import { toast } from "sonner";
import { LabelSchemaForm } from "@/components/LabelSchemaForm";
import { useCurrentUser } from "@/hooks/api-hooks";

export function ToolRenderer({
  item,
  traceData,
  reviewApp,
  session,
  currentIndex,
  totalItems,
  assessments,
  onAssessmentsChange,
  onUpdateItem,
  onNavigateToIndex,
  isLoading,
  isSubmitting,
}: ItemRendererProps) {
  // State for collapsible tool sections
  const [openTools, setOpenTools] = React.useState<Set<string>>(new Set());
  
  // Get current user
  const { data: currentUser } = useCurrentUser();
  const currentUsername = currentUser?.email || 'unknown';
  
  // Track last saved assessments to avoid duplicate saves
  const lastSavedAssessmentsRef = useRef<Map<string, Assessment>>(new Map());
  
  // React Query mutations for logging/updating assessments
  const logFeedbackMutation = useMutation({
    mutationFn: async ({ traceId, feedbackKey, feedbackValue, rationale }: {
      traceId: string;
      feedbackKey: string;
      feedbackValue: any;
      rationale?: string;
    }) => {
      return await MLflowService.logTraceFeedbackApiMlflowTracesTraceIdFeedbackPost(traceId, {
        feedback_key: feedbackKey,
        feedback_value: feedbackValue,
        rationale: rationale
      });
    },
    onError: (error) => {
      console.error('Failed to log feedback:', error);
      toast.error('Failed to save feedback. Please try again.');
    }
  });

  const updateFeedbackMutation = useMutation({
    mutationFn: async ({ traceId, assessmentId, feedbackValue, rationale }: {
      traceId: string;
      assessmentId: string;
      feedbackValue: any;
      rationale?: string;
    }) => {
      return await MLflowService.updateTraceFeedbackApiMlflowTracesTraceIdFeedbackPatch(traceId, {
        assessment_id: assessmentId,
        feedback_value: feedbackValue,
        rationale: rationale
      });
    },
    onError: (error) => {
      console.error('Failed to update feedback:', error);
      toast.error('Failed to update feedback. Please try again.');
    }
  });

  const logExpectationMutation = useMutation({
    mutationFn: async ({ traceId, expectationKey, expectationValue, rationale }: {
      traceId: string;
      expectationKey: string;
      expectationValue: any;
      rationale?: string;
    }) => {
      return await MLflowService.logTraceExpectationApiMlflowTracesTraceIdExpectationPost(traceId, {
        expectation_key: expectationKey,
        expectation_value: expectationValue,
        rationale: rationale
      });
    },
    onError: (error) => {
      console.error('Failed to log expectation:', error);
      toast.error('Failed to save expectation. Please try again.');
    }
  });
  
  const updateExpectationMutation = useMutation({
    mutationFn: async ({ traceId, assessmentId, expectationValue, rationale }: {
      traceId: string;
      assessmentId: string;
      expectationValue: any;
      rationale?: string;
    }) => {
      return await MLflowService.updateTraceExpectationApiMlflowTracesTraceIdExpectationPatch(traceId, {
        assessment_id: assessmentId,
        expectation_value: expectationValue,
        rationale: rationale
      });
    },
    onError: (error) => {
      console.error('Failed to update expectation:', error);
      toast.error('Failed to update expectation. Please try again.');
    }
  });
  
  // Handle saving a single assessment  
  const handleAssessmentSave = useCallback(async (assessment: Assessment) => {
    console.log('[AUTO-SAVE] Saving assessment:', assessment);
    
    // Get trace ID from item
    const traceId = item?.source?.trace_id;
    if (!traceId) {
      console.error('[AUTO-SAVE] No trace ID found in item');
      return;
    }
    
    // Check if this schema is relevant to the review app
    const relevantSchemaNames = new Set(reviewApp?.labeling_schemas?.map(schema => schema.name) || []);
    if (!relevantSchemaNames.has(assessment.name)) {
      console.log(`[AUTO-SAVE] Skipping assessment '${assessment.name}' - not relevant to current review app schemas`);
      return;
    }
    
    // Only save if there's either a value OR a rationale
    if ((assessment.value === undefined || assessment.value === null || assessment.value === "") &&
        (!assessment.rationale || assessment.rationale === "")) {
      console.log(`[AUTO-SAVE] Skipping empty assessment '${assessment.name}'`);
      return;
    }
    
    try {
      // Find the schema to determine if it's FEEDBACK or EXPECTATION
      const schema = reviewApp?.labeling_schemas?.find(s => s.name === assessment.name);
      const schemaType = schema?.type || 'FEEDBACK';
      
      let result: any;
      
      // Check if this assessment already exists (has an ID)
      const existingAssessment = assessments.get(assessment.name);
      const hasAssessmentId = existingAssessment?.assessment_id;
      
      // Check if the existing assessment belongs to the current user
      let shouldUpdate = false;
      if (hasAssessmentId && existingAssessment?.source) {
        const sourceId = typeof existingAssessment.source === 'object' 
          ? existingAssessment.source.source_id 
          : existingAssessment.source;
        shouldUpdate = sourceId === currentUsername;
        
        if (!shouldUpdate) {
          console.log(`[AUTO-SAVE] Cannot update assessment '${assessment.name}' - belongs to different user (${sourceId} vs ${currentUsername})`);
        }
      }
      
      if (schemaType === 'FEEDBACK') {
        if (shouldUpdate) {
          // Update existing feedback (only if owned by current user)
          result = await updateFeedbackMutation.mutateAsync({
            traceId,
            assessmentId: existingAssessment.assessment_id!,
            feedbackValue: assessment.value,
            rationale: assessment.rationale || undefined
          });
        } else {
          // Create new feedback (either no existing or belongs to different user)
          result = await logFeedbackMutation.mutateAsync({
            traceId,
            feedbackKey: assessment.name,
            feedbackValue: assessment.value,
            rationale: assessment.rationale || undefined
          });
        }
      } else {
        if (shouldUpdate) {
          // Update existing expectation (only if owned by current user)
          result = await updateExpectationMutation.mutateAsync({
            traceId,
            assessmentId: existingAssessment.assessment_id!,
            expectationValue: assessment.value,
            rationale: assessment.rationale || undefined
          });
        } else {
          // Create new expectation (either no existing or belongs to different user)
          result = await logExpectationMutation.mutateAsync({
            traceId,
            expectationKey: assessment.name,
            expectationValue: assessment.value,
            rationale: assessment.rationale || undefined
          });
        }
      }
      
      // Update parent's assessments with the new/updated assessment ID
      const newAssessments = new Map(assessments);
      const updatedAssessment = {
        ...assessment,
        assessment_id: result?.assessment_id || existingAssessment?.assessment_id
      };
      newAssessments.set(assessment.name, updatedAssessment);
      onAssessmentsChange(newAssessments);
      
      // Update last saved ref
      lastSavedAssessmentsRef.current.set(assessment.name, updatedAssessment);
      
      const action = shouldUpdate ? 'Updated' : 'Created';
      console.log(`[AUTO-SAVE] ${action} ${assessment.name}: ${assessment.value || 'rationale-only'} with rationale: ${assessment.rationale || 'none'}`);
      toast.success(`Auto-saved ${assessment.name}`, {
        duration: 2000,
      });
    } catch (error) {
      console.error(`[AUTO-SAVE] Failed to save ${assessment.name}:`, error);
      toast.error(`Failed to save ${assessment.name}. Please try again.`);
    }
  }, [item?.source?.trace_id, reviewApp?.labeling_schemas, assessments, onAssessmentsChange, logFeedbackMutation, logExpectationMutation, updateFeedbackMutation, updateExpectationMutation, currentUsername]);
  
  
  
  // Load existing assessments from trace data when item changes
  useEffect(() => {
    const loadExistingLabels = () => {
      console.log('DEBUG: traceData:', traceData);
      console.log('DEBUG: traceData.info:', traceData?.info);
      console.log('DEBUG: traceData.info.assessments:', traceData?.info?.assessments);
      console.log('DEBUG: item.source:', item?.source);
      
      // Add detailed assessment structure logging
      if (traceData?.info?.assessments) {
        traceData.info.assessments.forEach((assessment, index) => {
          console.log(`DEBUG: Assessment ${index}:`, {
            name: assessment.name,
            value: assessment.value,
            rationale: assessment.rationale,
            metadata: assessment.metadata,
            source: assessment.source,
            fullObject: assessment
          });
        });
      }
      
      if (!traceData?.info?.assessments || !reviewApp?.labeling_schemas) {
        console.log('No assessments found in trace data or no labeling schemas');
        onAssessmentsChange(new Map());
        lastSavedAssessmentsRef.current = new Map();
        return;
      }
      
      const assessments: Assessment[] = traceData.info.assessments;
      console.log('Loading existing assessments from trace data:', assessments);
      
      // Get the schema names that are relevant to this review app
      const relevantSchemaNames = new Set(reviewApp.labeling_schemas.map(schema => schema.name));
      console.log('Relevant schema names for this review app:', relevantSchemaNames);
      
      // Group assessments by name and prioritize current user's assessments
      const assessmentsByName = new Map<string, Assessment>();
      
      assessments.forEach((assessment) => {
        // Only process assessments that belong to this review app's schemas
        if (!relevantSchemaNames.has(assessment.name)) {
          console.log(`Skipping assessment '${assessment.name}' - not relevant to current review app schemas`);
          return;
        }
        
        // Check for rationale in metadata (MLflow bug workaround)
        const rationale = assessment.metadata?.rationale || assessment.rationale;
        
        // Get the source ID (email) from the assessment
        const sourceId = typeof assessment.source === 'object' 
          ? assessment.source.source_id 
          : assessment.source;
        
        const isCurrentUser = sourceId === currentUsername;
        
        // Keep the assessment if:
        // 1. It's from the current user (prioritize user's own assessments)
        // 2. OR there's no existing assessment for this name
        // 3. OR the existing assessment is NOT from the current user (replace with current user's)
        const existing = assessmentsByName.get(assessment.name);
        const existingIsCurrentUser = existing?.source && (
          typeof existing.source === 'object' 
            ? existing.source.source_id === currentUsername
            : existing.source === currentUsername
        );
        
        if (isCurrentUser || !existing || !existingIsCurrentUser) {
          // Only replace if this is the current user's assessment or there's no current user assessment
          if (isCurrentUser || !existingIsCurrentUser) {
            assessmentsByName.set(assessment.name, {
              ...assessment,
              rationale: rationale,
              assessment_id: assessment.assessment_id || assessment.id  // Include assessment ID
            });
            console.log(`Loaded assessment ${assessment.name} from user ${sourceId}`);
          }
        }
      });
      
      // Update the form with existing assessments (only relevant ones)
      if (assessmentsByName.size > 0) {
        console.log('Populating form with relevant existing assessments:', assessmentsByName);
        assessmentsByName.forEach((assessment) => {
          console.log(`Loaded assessment ${assessment.name}: value=${assessment.value}, rationale=${assessment.rationale}`);
        });
        onAssessmentsChange(assessmentsByName);
        lastSavedAssessmentsRef.current = assessmentsByName;
      } else {
        onAssessmentsChange(new Map());
        lastSavedAssessmentsRef.current = new Map();
      }
    };
    
    loadExistingLabels();
  }, [item?.item_id, traceData?.info?.assessments, reviewApp?.labeling_schemas, onAssessmentsChange, currentUsername]);
  
  // Extract spans, filtering for conversational spans
  const allSpans = traceData?.spans || [];
  
  // Helper function to get span type
  const getSpanType = (span: any) => {
    return span.span_type || span.attributes?.['mlflow.spanType'] || 'UNKNOWN';
  };
  
  // Filter for conversational spans - include USER, ASSISTANT, AGENT, CHAT_MODEL, and TOOL spans
  const spans = allSpans.filter((span) => {
    const spanType = getSpanType(span);
    return ['CHAT_MODEL', 'TOOL', 'AGENT', 'LLM', 'USER', 'ASSISTANT'].includes(spanType);
  });
  
  // Helper function to extract user message for deduplication
  const getUserMessage = (span: any) => {
    const spanType = getSpanType(span);
    if (spanType === 'TOOL') return null;
    
    // Check for chat messages in attributes
    if (span.attributes?.['mlflow.chat.messages']) {
      const messages = span.attributes['mlflow.chat.messages'];
      const userMessage = messages.find((msg: any) => msg.role === 'user');
      return userMessage?.content || null;
    }
    
    // Check inputs
    const inputs = span.inputs;
    if (inputs?.messages) {
      const userMessage = inputs.messages.find((msg: any) => msg.role === 'user');
      return userMessage?.content || null;
    }
    
    // For simple inputs, check if it's a user message
    if (typeof inputs === 'string') {
      return inputs;
    }
    
    return null;
  };
  
  // Deduplicate conversation spans by user message content
  const seenUserMessages = new Set<string>();
  const deduplicatedSpans = spans.filter((span) => {
    const spanType = getSpanType(span);
    
    // Always include tool spans
    if (spanType === 'TOOL') {
      return true;
    }
    
    // For conversation spans, check if we've seen this user message before
    const userMessage = getUserMessage(span);
    if (userMessage && seenUserMessages.has(userMessage)) {
      return false; // Skip duplicate conversation
    }
    
    if (userMessage) {
      seenUserMessages.add(userMessage);
    }
    
    return true;
  });
  
  // Separate spans by type for chronological rendering
  const conversationSpans = deduplicatedSpans.filter(span => getSpanType(span) !== 'TOOL');
  const toolSpans = deduplicatedSpans.filter(span => getSpanType(span) === 'TOOL');
  
  // Extract user request and assistant response from conversation spans
  let userRequest = null;
  let assistantResponse = null;
  
  for (const span of conversationSpans) {
    const spanType = getSpanType(span);
    
    // Try to get user message
    if (!userRequest) {
      if (span.attributes?.['mlflow.chat.messages']) {
        const messages = span.attributes['mlflow.chat.messages'];
        const userMessage = messages.find((msg: any) => msg.role === 'user');
        if (userMessage) {
          userRequest = { content: userMessage.content, span };
        }
      } else if (span.inputs?.messages) {
        const userMessage = span.inputs.messages.find((msg: any) => msg.role === 'user');
        if (userMessage) {
          userRequest = { content: userMessage.content, span };
        }
      } else if (span.inputs && typeof span.inputs === 'string') {
        userRequest = { content: span.inputs, span };
      }
    }
    
    // Try to get assistant response (prefer the one with most complete response)
    if (span.outputs) {
      if (span.outputs.choices?.[0]?.message?.content) {
        assistantResponse = { content: span.outputs.choices[0].message.content, span };
      } else if (typeof span.outputs === 'string') {
        assistantResponse = { content: span.outputs, span };
      } else if (span.outputs.output) {
        assistantResponse = { content: span.outputs.output, span };
      }
    }
  }
  
  const toggleTool = (toolId: string) => {
    setOpenTools(prev => {
      const newSet = new Set(prev);
      if (newSet.has(toolId)) {
        newSet.delete(toolId);
      } else {
        newSet.add(toolId);
      }
      return newSet;
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left column: Conversation */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Conversation</h3>
        
        <div className="space-y-4">
          {/* Render chronologically: User Request → Tools → Assistant Response */}
          
          {/* User Request */}
          {userRequest && (
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm mb-1">User</div>
                <div className="text-sm">
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>{userRequest.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tools Used */}
          {toolSpans.length > 0 && (
            <div className="ml-11 space-y-2">
              {toolSpans.map((toolSpan, toolIdx) => {
                const toolId = `tool-${toolIdx}`;
                const isOpen = openTools.has(toolId);
                
                return (
                  <Collapsible key={toolId} open={isOpen} onOpenChange={() => toggleTool(toolId)}>
                    <CollapsibleTrigger className="flex items-center justify-between p-3 hover:bg-muted/50 rounded-lg border w-full">
                      <div className="flex items-center gap-3">
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        )}
                        <Wrench className="h-4 w-4" />
                        <span className="font-medium text-sm">{toolSpan.name}</span>
                      </div>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent>
                      <div className="p-4 bg-muted/20 ml-7 space-y-4">
                        {toolSpan.inputs && (
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground font-medium">Input:</div>
                            <div className="bg-background border rounded-lg p-3">
                              <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                                {typeof toolSpan.inputs === "string"
                                  ? toolSpan.inputs
                                  : JSON.stringify(toolSpan.inputs, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
                        
                        {toolSpan.outputs && (
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground font-medium">Output:</div>
                            <div className="bg-background border rounded-lg p-3">
                              {typeof toolSpan.outputs === "string" ? (
                                <div className="prose prose-slate prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-50 dark:prose-pre:bg-gray-900 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-ul:list-disc prose-ol:list-decimal prose-li:marker:text-gray-500">
                                  <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeHighlight]}
                                    components={{
                                      h1: ({children}) => <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3 pb-1 border-b border-gray-200 dark:border-gray-700">{children}</h1>,
                                      h2: ({children}) => <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2 mt-4 pb-1 border-b border-gray-200 dark:border-gray-700">{children}</h2>,
                                      h3: ({children}) => <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 mt-3">{children}</h3>,
                                      p: ({children}) => <p className="text-gray-700 dark:text-gray-300 mb-2 leading-relaxed">{children}</p>,
                                      ul: ({children}) => <ul className="list-disc pl-4 mb-3 text-gray-700 dark:text-gray-300">{children}</ul>,
                                      ol: ({children}) => <ol className="list-decimal pl-4 mb-3 text-gray-700 dark:text-gray-300">{children}</ol>,
                                      li: ({children}) => <li className="text-gray-700 dark:text-gray-300">{children}</li>,
                                      strong: ({children}) => <strong className="font-semibold text-gray-900 dark:text-gray-100">{children}</strong>,
                                      blockquote: ({children}) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 dark:text-gray-400 my-3">{children}</blockquote>,
                                    }}
                                  >
                                    {toolSpan.outputs}
                                  </ReactMarkdown>
                                </div>
                              ) : (
                                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                                  {JSON.stringify(toolSpan.outputs, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                );
              })}
            </div>
          )}

          {/* Assistant Response */}
          {assistantResponse && (
            <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
              <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm mb-1">Assistant</div>
                <div className="text-sm">
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>{assistantResponse.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right column: Separated Feedback and Expectations */}
      <div className="space-y-6">
        {/* Feedback schemas */}
        {reviewApp?.labeling_schemas?.filter(schema => schema.type === 'FEEDBACK').length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Feedback</h3>
            <LabelSchemaForm
              schemas={reviewApp.labeling_schemas.filter(schema => schema.type === 'FEEDBACK')}
              assessments={assessments}
              onAssessmentSave={handleAssessmentSave}
              readOnly={false}
            />
          </div>
        )}

        {/* Expectation schemas */}
        {reviewApp?.labeling_schemas?.filter(schema => schema.type === 'EXPECTATION').length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Expectations</h3>
            <LabelSchemaForm
              schemas={reviewApp.labeling_schemas.filter(schema => schema.type === 'EXPECTATION')}
              assessments={assessments}
              onAssessmentSave={handleAssessmentSave}
              readOnly={false}
            />
          </div>
        )}
      </div>

      {/* Actions - Full width section below the grid */}
      <div className="col-span-1 lg:col-span-2 flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={() => {
            if (currentIndex > 0) {
              onNavigateToIndex(currentIndex - 1);
            }
          }}
          disabled={currentIndex === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>

        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={async () => {
              // Mark as skipped and move to next
              await onUpdateItem(item.item_id, { state: "SKIPPED" });
              if (currentIndex < totalItems - 1) {
                onNavigateToIndex(currentIndex + 1);
              }
            }}
            disabled={isSubmitting}
          >
            <XCircle className="h-4 w-4 mr-2" />
            Skip
          </Button>
          <Button
            onClick={async () => {
              // Assessments are already saved via auto-save
              // Just mark as completed and move to next
              await onUpdateItem(item.item_id, { state: "COMPLETED" });
              toast.success('Review completed');
              if (currentIndex < totalItems - 1) {
                onNavigateToIndex(currentIndex + 1);
              }
            }}
            disabled={isSubmitting || assessments.size === 0}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Submit & Next
          </Button>
        </div>
      </div>
    </div>
  );
}