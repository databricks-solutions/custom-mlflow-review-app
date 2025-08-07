import React, { useCallback, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  XCircle,
  Check,
  Circle,
  ChevronDown,
  ChevronRight,
  Wrench,
  User,
  Bot,
} from "lucide-react";
import { ItemRendererProps } from "@/types/renderers";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { useMutation } from "@tanstack/react-query";
import { MLflowService } from "@/fastapi_client";
import { toast } from "sonner";
// Removed TraceAssessmentsService import - assessments now come from trace data

export function ToolRenderer({
  item,
  traceData,
  reviewApp,
  session,
  currentIndex,
  totalItems,
  labels,
  onLabelsChange,
  onUpdateItem,
  onNavigateToIndex,
  isLoading,
  isSubmitting,
}: ItemRendererProps) {
  // State for collapsible tool sections
  const [openTools, setOpenTools] = React.useState<Set<string>>(new Set());
  
  // Auto-save refs
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedLabelsRef = useRef<string>("");
  
  // React Query mutations for logging assessments
  const logFeedbackMutation = useMutation({
    mutationFn: async ({ traceId, feedbackKey, feedbackValue, feedbackComment }: {
      traceId: string;
      feedbackKey: string;
      feedbackValue: any;
      feedbackComment?: string;
    }) => {
      return await MLflowService.logTraceFeedbackApiMlflowTracesTraceIdFeedbackPost(traceId, {
        feedback_key: feedbackKey,
        feedback_value: feedbackValue,
        feedback_comment: feedbackComment
      });
    },
    onError: (error) => {
      console.error('Failed to log feedback:', error);
      toast.error('Failed to save feedback. Please try again.');
    }
  });

  const logExpectationMutation = useMutation({
    mutationFn: async ({ traceId, expectationKey, expectationValue, expectationComment }: {
      traceId: string;
      expectationKey: string;
      expectationValue: any;
      expectationComment?: string;
    }) => {
      return await MLflowService.logTraceExpectationApiMlflowTracesTraceIdExpectationPost(traceId, {
        expectation_key: expectationKey,
        expectation_value: expectationValue,
        expectation_comment: expectationComment
      });
    },
    onError: (error) => {
      console.error('Failed to log expectation:', error);
      toast.error('Failed to save expectation. Please try again.');
    }
  });
  
  // Helper function to convert flat labels to API format
  const convertLabelsToApiFormat = (flatLabels: Record<string, any>) => {
    const apiLabels: Record<string, any> = {};
    
    // Convert flat structure to nested structure expected by API
    Object.keys(flatLabels).forEach(key => {
      if (key.endsWith('_comment')) {
        // Skip comment fields - they'll be handled with their parent
        return;
      }
      
      const commentKey = `${key}_comment`;
      const value = flatLabels[key];
      
      if (value !== undefined && value !== null && value !== "") {
        apiLabels[key] = {
          value: value,
          ...(flatLabels[commentKey] ? { comment: flatLabels[commentKey] } : {})
        };
      }
    });
    
    return apiLabels;
  };
  
  // Auto-save functionality - save to MLflow when labels change
  const handleLabelsChange = useCallback(async (newLabels: Record<string, any>) => {
    onLabelsChange(newLabels);
    
    // Clear any existing timeout to debounce the save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Set a new timeout to save after 2 seconds of no changes
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        console.log('[AUTO-SAVE] Starting auto-save for labels:', newLabels);
        
        // Get trace ID from item
        const traceId = item.source?.trace_id;
        if (!traceId) {
          console.error('[AUTO-SAVE] No trace ID found in item');
          return;
        }
        
        // Get the schema names that are relevant to this review app
        const relevantSchemaNames = new Set(reviewApp?.labeling_schemas?.map(schema => schema.name) || []);
        
        // Convert labels to API format and save each assessment, but ONLY for relevant schemas
        const apiLabels = convertLabelsToApiFormat(newLabels);
        let savedCount = 0;
        
        for (const [schemaName, labelData] of Object.entries(apiLabels)) {
          // Only save assessments that belong to this review app's schemas
          if (!relevantSchemaNames.has(schemaName)) {
            console.log(`[AUTO-SAVE] Skipping assessment '${schemaName}' - not relevant to current review app schemas`);
            continue;
          }
          
          if (labelData.value !== undefined && labelData.value !== null && labelData.value !== "") {
            try {
              // Find the schema to determine if it's FEEDBACK or EXPECTATION
              const schema = reviewApp?.labeling_schemas?.find(s => s.name === schemaName);
              const schemaType = schema?.type || 'FEEDBACK';
              
              if (schemaType === 'FEEDBACK') {
                await logFeedbackMutation.mutateAsync({
                  traceId,
                  feedbackKey: schemaName,
                  feedbackValue: labelData.value,
                  feedbackComment: labelData.comment
                });
              } else {
                await logExpectationMutation.mutateAsync({
                  traceId,
                  expectationKey: schemaName,
                  expectationValue: labelData.value,
                  expectationComment: labelData.comment
                });
              }
              savedCount++;
              console.log(`[AUTO-SAVE] Saved ${schemaName}: ${labelData.value}`);
            } catch (error) {
              console.error(`[AUTO-SAVE] Failed to save ${schemaName}:`, error);
            }
          }
        }
        
        if (savedCount > 0) {
          console.log(`[AUTO-SAVE] Successfully auto-saved ${savedCount} assessments`);
          // Show subtle feedback that auto-save worked
          toast.success(`Auto-saved ${savedCount} assessment${savedCount > 1 ? 's' : ''}`, {
            duration: 2000,
          });
        }
        
      } catch (error) {
        console.error('[AUTO-SAVE] Auto-save failed:', error);
      }
    }, 2000); // Auto-save after 2 seconds of no changes
    
  }, [onLabelsChange, item.source?.trace_id, reviewApp?.labeling_schemas, logFeedbackMutation, logExpectationMutation, convertLabelsToApiFormat]);
  
  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);
  
  // Helper function to convert API format labels to flat structure for UI
  const convertLabelsFromApiFormat = (apiLabels: Record<string, any>) => {
    const flatLabels: Record<string, any> = {};
    
    Object.keys(apiLabels).forEach(key => {
      const labelData = apiLabels[key];
      if (typeof labelData === 'object' && labelData !== null) {
        // New format: { value: ..., comment: ... }
        if (labelData.value !== undefined) {
          flatLabels[key] = labelData.value;
        }
        if (labelData.comment) {
          flatLabels[`${key}_comment`] = labelData.comment;
        }
      } else {
        // Old format or direct value
        flatLabels[key] = labelData;
      }
    });
    
    return flatLabels;
  };
  
  // Load existing assessments from trace data when item changes
  useEffect(() => {
    const loadExistingLabels = () => {
      console.log('DEBUG: traceData:', traceData);
      console.log('DEBUG: traceData.info:', traceData?.info);
      console.log('DEBUG: traceData.info.assessments:', traceData?.info?.assessments);
      console.log('DEBUG: item.source:', item?.source);
      
      if (!traceData?.info?.assessments || !reviewApp?.labeling_schemas) {
        console.log('No assessments found in trace data or no labeling schemas');
        onLabelsChange({});
        lastSavedLabelsRef.current = "";
        return;
      }
      
      const assessments = traceData.info.assessments;
      console.log('Loading existing assessments from trace data:', assessments);
      
      // Get the schema names that are relevant to this review app
      const relevantSchemaNames = new Set(reviewApp.labeling_schemas.map(schema => schema.name));
      console.log('Relevant schema names for this review app:', relevantSchemaNames);
      
      // Convert assessments to flat format for UI, but ONLY include assessments for relevant schemas
      const flatLabels: Record<string, any> = {};
      assessments.forEach((assessment: any) => {
        const key = assessment.name;
        
        // Only process assessments that belong to this review app's schemas
        if (!relevantSchemaNames.has(key)) {
          console.log(`Skipping assessment '${key}' - not relevant to current review app schemas`);
          return;
        }
        
        // Extract value from nested structure (feedback/expectation) OR direct value
        let assessmentValue = null;
        if (assessment.feedback) {
          assessmentValue = assessment.feedback.value;
        } else if (assessment.expectation) {
          assessmentValue = assessment.expectation.value;
        } else if (assessment.value !== undefined) {
          // Direct value format (what our API currently returns)
          assessmentValue = assessment.value;
        }
        
        if (assessmentValue !== null && assessmentValue !== undefined) {
          flatLabels[key] = assessmentValue;
        }
        
        // Add rationale/comment if present (check both rationale and comment fields)
        if (assessment.rationale) {
          flatLabels[`${key}_comment`] = assessment.rationale;
        } else if (assessment.comment) {
          flatLabels[`${key}_comment`] = assessment.comment;
        }
      });
      
      // Update the form with existing labels (only relevant ones)
      if (Object.keys(flatLabels).length > 0) {
        console.log('Populating form with relevant existing assessments:', flatLabels);
        onLabelsChange(flatLabels);
        lastSavedLabelsRef.current = JSON.stringify(convertLabelsToApiFormat(flatLabels));
      } else {
        onLabelsChange({});
        lastSavedLabelsRef.current = "";
      }
    };
    
    loadExistingLabels();
  }, [item?.item_id, traceData?.info?.assessments, reviewApp?.labeling_schemas, onLabelsChange]);
  
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
            <div className="space-y-4">
              <Accordion type="single" collapsible className="w-full">
                {reviewApp?.labeling_schemas?.filter(schema => schema.type === 'FEEDBACK').map((schema) => {
                  const hasValue = labels[schema.name] !== undefined && labels[schema.name] !== null && labels[schema.name] !== "";
                  const isCompleted = hasValue;
                  
                  return (
                    <AccordionItem key={schema.name} value={schema.name} className="border rounded-lg px-4">
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-2">
                          {isCompleted ? (
                            <Check className="h-4 w-4 text-green-600" />
                          ) : (
                            <Circle className="h-4 w-4 text-green-600" />
                          )}
                          <span>{schema.title || schema.name}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pt-4">
                        {schema.instruction && (
                          <p className="text-sm text-muted-foreground">{schema.instruction}</p>
                        )}

                        {schema.numeric && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm">{schema.numeric.min_value}</span>
                              <span className="text-lg font-semibold">
                                {labels[schema.name] || schema.numeric.min_value}
                              </span>
                              <span className="text-sm">{schema.numeric.max_value}</span>
                            </div>
                            <Slider
                              value={[labels[schema.name] || schema.numeric.min_value]}
                              onValueChange={(value) => handleLabelsChange({ ...labels, [schema.name]: value[0] })}
                              min={schema.numeric.min_value}
                              max={schema.numeric.max_value}
                              step={1}
                            />
                          </div>
                        )}

                        {schema.categorical && (
                          <RadioGroup
                            value={labels[schema.name]}
                            onValueChange={(value) => handleLabelsChange({ ...labels, [schema.name]: value })}
                          >
                            {schema.categorical.options?.map((option) => (
                              <div key={option} className="flex items-center space-x-2">
                                <RadioGroupItem value={option} id={`${schema.name}-${option}`} />
                                <Label htmlFor={`${schema.name}-${option}`}>{option}</Label>
                              </div>
                            ))}
                          </RadioGroup>
                        )}

                        {schema.text && (
                          <div className="space-y-2">
                            <Label htmlFor={schema.name}>Response</Label>
                            <Textarea
                              id={schema.name}
                              value={labels[schema.name] || ""}
                              onChange={(e) => handleLabelsChange({ ...labels, [schema.name]: e.target.value })}
                              placeholder={schema.text.placeholder || "Enter your response..."}
                              rows={4}
                            />
                          </div>
                        )}

                        {schema.enable_comment && (
                          <div className="space-y-2 pt-2 border-t">
                            <Label htmlFor={`${schema.name}_comment`}>Comments</Label>
                            <Textarea
                              id={`${schema.name}_comment`}
                              value={labels[`${schema.name}_comment`] || ""}
                              onChange={(e) => handleLabelsChange({ ...labels, [`${schema.name}_comment`]: e.target.value })}
                              placeholder="Add your reasoning or additional feedback..."
                              rows={2}
                            />
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </div>
          </div>
        )}

        {/* Expectation schemas */}
        {reviewApp?.labeling_schemas?.filter(schema => schema.type === 'EXPECTATION').length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Expectations</h3>
            <div className="space-y-4">
              <Accordion type="single" collapsible className="w-full">
                {reviewApp?.labeling_schemas?.filter(schema => schema.type === 'EXPECTATION').map((schema) => {
                  const hasValue = labels[schema.name] !== undefined && labels[schema.name] !== null && labels[schema.name] !== "";
                  const isCompleted = hasValue;
                  
                  return (
                    <AccordionItem key={schema.name} value={schema.name} className="border rounded-lg px-4">
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-2">
                          {isCompleted ? (
                            <Check className="h-4 w-4 text-blue-600" />
                          ) : (
                            <Circle className="h-4 w-4 text-blue-600" />
                          )}
                          <span>{schema.title || schema.name}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pt-4">
                        {schema.instruction && (
                          <p className="text-sm text-muted-foreground">{schema.instruction}</p>
                        )}

                        {schema.numeric && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm">{schema.numeric.min_value}</span>
                              <span className="text-lg font-semibold">
                                {labels[schema.name] || schema.numeric.min_value}
                              </span>
                              <span className="text-sm">{schema.numeric.max_value}</span>
                            </div>
                            <Slider
                              value={[labels[schema.name] || schema.numeric.min_value]}
                              onValueChange={(value) => handleLabelsChange({ ...labels, [schema.name]: value[0] })}
                              min={schema.numeric.min_value}
                              max={schema.numeric.max_value}
                              step={1}
                            />
                          </div>
                        )}

                        {schema.categorical && (
                          <RadioGroup
                            value={labels[schema.name]}
                            onValueChange={(value) => handleLabelsChange({ ...labels, [schema.name]: value })}
                          >
                            {schema.categorical.options?.map((option) => (
                              <div key={option} className="flex items-center space-x-2">
                                <RadioGroupItem value={option} id={`${schema.name}-${option}`} />
                                <Label htmlFor={`${schema.name}-${option}`}>{option}</Label>
                              </div>
                            ))}
                          </RadioGroup>
                        )}

                        {schema.text && (
                          <div className="space-y-2">
                            <Label htmlFor={schema.name}>Response</Label>
                            <Textarea
                              id={schema.name}
                              value={labels[schema.name] || ""}
                              onChange={(e) => handleLabelsChange({ ...labels, [schema.name]: e.target.value })}
                              placeholder={schema.text.placeholder || "Enter your response..."}
                              rows={4}
                            />
                          </div>
                        )}

                        {schema.enable_comment && (
                          <div className="space-y-2 pt-2 border-t">
                            <Label htmlFor={`${schema.name}_comment`}>Comments</Label>
                            <Textarea
                              id={`${schema.name}_comment`}
                              value={labels[`${schema.name}_comment`] || ""}
                              onChange={(e) => handleLabelsChange({ ...labels, [`${schema.name}_comment`]: e.target.value })}
                              placeholder="Add your reasoning or additional expectations..."
                              rows={2}
                            />
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </div>
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
              if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
              }
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
              // Log assessments to trace via MLflow API
              if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
              }
              
              // Get trace ID from item
              const traceId = item.source?.trace_id;
              if (!traceId) {
                console.error('No trace ID found in item');
                return;
              }

              try {
                // Get the schema names that are relevant to this review app
                const relevantSchemaNames = new Set(reviewApp?.labeling_schemas?.map(schema => schema.name) || []);
                
                // Convert each label to MLflow assessment, but ONLY for relevant schemas
                const apiLabels = convertLabelsToApiFormat(labels);
                
                // Track success count for feedback
                let successCount = 0;
                let totalCount = 0;
                
                // Log all assessments in parallel (only relevant ones)
                const assessmentPromises = Object.entries(apiLabels).map(async ([schemaName, labelData]) => {
                  // Only process assessments that belong to this review app's schemas
                  if (!relevantSchemaNames.has(schemaName)) {
                    console.log(`[SUBMIT] Skipping assessment '${schemaName}' - not relevant to current review app schemas`);
                    return;
                  }
                  
                  if (labelData.value !== undefined && labelData.value !== null && labelData.value !== "") {
                    totalCount++;
                    // Find the schema to determine if it's FEEDBACK or EXPECTATION
                    const schema = reviewApp?.labeling_schemas?.find(s => s.name === schemaName);
                    const schemaType = schema?.type || 'FEEDBACK';
                    
                    try {
                      if (schemaType === 'FEEDBACK') {
                        // Log as feedback using React Query mutation
                        await logFeedbackMutation.mutateAsync({
                          traceId,
                          feedbackKey: schemaName,
                          feedbackValue: labelData.value,
                          feedbackComment: labelData.comment
                        });
                        successCount++;
                      } else {
                        // Log as expectation using React Query mutation
                        await logExpectationMutation.mutateAsync({
                          traceId,
                          expectationKey: schemaName,
                          expectationValue: labelData.value,
                          expectationComment: labelData.comment
                        });
                        successCount++;
                      }
                    } catch (error) {
                      // Individual assessment failed, but continue with others
                      console.error(`Failed to log assessment for ${schemaName}:`, error);
                    }
                  }
                });
                
                // Wait for all assessments to be logged
                await Promise.all(assessmentPromises);
                
                // Show appropriate feedback based on success
                if (successCount === totalCount && totalCount > 0) {
                  toast.success('All feedback saved successfully');
                } else if (successCount > 0) {
                  toast.warning(`Saved ${successCount} of ${totalCount} feedback items`);
                } else if (totalCount > 0) {
                  toast.error('Failed to save feedback. Please try again.');
                }
                
                // Mark item as completed (without labels)
                await onUpdateItem(item.item_id, { state: "COMPLETED" });
                
                // Move to next item
                if (currentIndex < totalItems - 1) {
                  onNavigateToIndex(currentIndex + 1);
                }
              } catch (error) {
                console.error('Failed to submit assessments:', error);
                toast.error('An unexpected error occurred. Moving to next item.');
                // Still mark as completed even if some assessments failed
                await onUpdateItem(item.item_id, { state: "COMPLETED" });
                if (currentIndex < totalItems - 1) {
                  onNavigateToIndex(currentIndex + 1);
                }
              }
            }}
            disabled={isSubmitting || Object.keys(labels).length === 0 || logFeedbackMutation.isPending || logExpectationMutation.isPending}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Submit & Next
          </Button>
        </div>
      </div>
    </div>
  );
}