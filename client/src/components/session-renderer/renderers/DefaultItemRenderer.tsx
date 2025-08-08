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
import { ArrowLeft, CheckCircle, XCircle, Check, Circle, User, Bot } from "lucide-react";
import { ItemRendererProps } from "@/types/renderers";
import { Assessment } from "@/types/assessment";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { toast } from "sonner";
import { useLogFeedbackMutation, useLogExpectationMutation } from "@/hooks/shared-hooks";
import { useCurrentUser } from "@/hooks/api-hooks";
import {
  combineSchemaWithAssessments,
  filterByType,
  isSchemaCompleted,
} from "@/utils/schema-assessment-utils";

// Constants for span type filtering
const CONVERSATIONAL_SPAN_TYPES = ["CHAT_MODEL", "TOOL", "AGENT", "LLM", "USER", "ASSISTANT"];

export function DefaultItemRenderer({
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
  // Auto-save refs
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedAssessmentsRef = useRef<Map<string, Assessment>>(new Map());

  // React Query mutations for logging assessments
  const logFeedbackMutation = useLogFeedbackMutation();
  const logExpectationMutation = useLogExpectationMutation();

  // Combine schemas with assessments from trace data
  const schemasWithAssessments = combineSchemaWithAssessments(
    reviewApp?.labeling_schemas || [],
    traceData?.info?.assessments as Assessment[] | undefined
  );

  // Separate feedback and expectation schemas
  const feedbackSchemas = filterByType(schemasWithAssessments, "FEEDBACK");
  const expectationSchemas = filterByType(schemasWithAssessments, "EXPECTATION");

  // Helper function to handle assessment changes
  const handleAssessmentChange = (schemaName: string, value: any, rationale?: string) => {
    const newAssessments = new Map(assessments);
    const assessment: Assessment = {
      name: schemaName,
      value,
      rationale,
      timestamp: new Date().toISOString(),
      user: currentUser?.email || "unknown",
    };
    newAssessments.set(schemaName, assessment);
    onAssessmentsChange(newAssessments);
  };

  // Get current user
  const { data: currentUser } = useCurrentUser();

  // Auto-save functionality - save to MLflow when assessments change
  useEffect(() => {
    const saveAssessments = async () => {
      // Only proceed if assessments have changed
      const hasChanges = Array.from(assessments.entries()).some(([key, assessment]) => {
        const lastSaved = lastSavedAssessmentsRef.current.get(key);
        return (
          !lastSaved ||
          lastSaved.value !== assessment.value ||
          lastSaved.rationale !== assessment.rationale
        );
      });

      if (!hasChanges) return;

      // Clear any existing timeout to debounce the save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Set a new timeout to save after 2 seconds of no changes
      saveTimeoutRef.current = setTimeout(async () => {
        try {
          console.log("[AUTO-SAVE] Starting auto-save for assessments");

          // Get trace ID from item
          const traceId = item.source?.trace_id;
          if (!traceId) {
            console.error("[AUTO-SAVE] No trace ID found in item");
            return;
          }

          let savedCount = 0;

          for (const [schemaName, assessment] of assessments.entries()) {
            // Skip if assessment hasn't changed
            const lastSaved = lastSavedAssessmentsRef.current.get(schemaName);
            if (
              lastSaved &&
              lastSaved.value === assessment.value &&
              lastSaved.rationale === assessment.rationale
            ) {
              continue;
            }

            // Save if there's either a value OR a rationale
            if (
              (assessment.value !== undefined &&
                assessment.value !== null &&
                assessment.value !== "") ||
              (assessment.rationale && assessment.rationale !== "")
            ) {
              try {
                // Find the schema to determine if it's FEEDBACK or EXPECTATION
                const schema = reviewApp?.labeling_schemas?.find((s) => s.name === schemaName);
                const schemaType = schema?.type || "FEEDBACK";

                if (schemaType === "FEEDBACK") {
                  await logFeedbackMutation.mutateAsync({
                    traceId,
                    feedbackKey: schemaName,
                    feedbackValue: assessment.value,
                    rationale: assessment.rationale,
                  });
                } else {
                  await logExpectationMutation.mutateAsync({
                    traceId,
                    expectationKey: schemaName,
                    expectationValue: assessment.value,
                    rationale: assessment.rationale,
                  });
                }
                savedCount++;
                console.log(
                  `[AUTO-SAVE] Saved ${schemaName}: ${assessment.value || "rationale-only"} with rationale: ${assessment.rationale || "none"}`
                );
              } catch (error) {
                console.error(`[AUTO-SAVE] Failed to save ${schemaName}:`, error);
              }
            }
          }

          if (savedCount > 0) {
            console.log(`[AUTO-SAVE] Successfully auto-saved ${savedCount} assessments`);
            // Update last saved reference
            lastSavedAssessmentsRef.current = new Map(assessments);
            // Show subtle feedback that auto-save worked
            toast.success(`Auto-saved ${savedCount} assessment${savedCount > 1 ? "s" : ""}`, {
              duration: 2000,
            });
          }
        } catch (error) {
          console.error("[AUTO-SAVE] Auto-save failed:", error);
        }
      }, 2000); // Auto-save after 2 seconds of no changes
    };

    saveAssessments();
  }, [
    assessments,
    item.source?.trace_id,
    reviewApp?.labeling_schemas,
    logFeedbackMutation,
    logExpectationMutation,
  ]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Extract spans, filtering for conversational spans
  const allSpans = traceData?.spans || [];

  // Helper function to get span type
  const getSpanType = (span: any) => {
    return span.span_type || span.attributes?.["mlflow.spanType"] || "UNKNOWN";
  };

  // Filter for conversational spans
  const spans = allSpans.filter((span) => {
    const spanType = getSpanType(span);
    return CONVERSATIONAL_SPAN_TYPES.includes(spanType);
  });

  // Helper function to extract user message for deduplication
  const getUserMessage = (span: any) => {
    const spanType = getSpanType(span);
    if (spanType === "TOOL") return null;

    // Check for chat messages in attributes
    if (span.attributes?.["mlflow.chat.messages"]) {
      const messages = span.attributes["mlflow.chat.messages"];
      const userMessage = messages.find((msg: any) => msg.role === "user");
      return userMessage?.content || null;
    }

    // Check inputs
    const inputs = span.inputs;
    if (inputs?.messages) {
      const userMessage = inputs.messages.find((msg: any) => msg.role === "user");
      return userMessage?.content || null;
    }

    // For simple inputs, check if it's a user message
    if (typeof inputs === "string") {
      return inputs;
    }

    return null;
  };

  // Deduplicate conversation spans by user message content
  const seenUserMessages = new Set<string>();
  const deduplicatedSpans = spans.filter((span) => {
    const spanType = getSpanType(span);

    // Always include tool spans
    if (spanType === "TOOL") {
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
  const conversationSpans = deduplicatedSpans.filter((span) => getSpanType(span) !== "TOOL");
  const toolSpans = deduplicatedSpans.filter((span) => getSpanType(span) === "TOOL");

  // Extract user request and assistant response from conversation spans
  let userRequest = null;
  let assistantResponse = null;

  for (const span of conversationSpans) {
    const spanType = getSpanType(span);

    // Try to get user message
    if (!userRequest) {
      if (span.attributes?.["mlflow.chat.messages"]) {
        const messages = span.attributes["mlflow.chat.messages"];
        const userMessage = messages.find((msg: any) => msg.role === "user");
        if (userMessage) {
          userRequest = { content: userMessage.content, span };
        }
      } else if (span.inputs?.messages) {
        const userMessage = span.inputs.messages.find((msg: any) => msg.role === "user");
        if (userMessage) {
          userRequest = { content: userMessage.content, span };
        }
      } else if (span.inputs && typeof span.inputs === "string") {
        userRequest = { content: span.inputs, span };
      }
    }

    // Try to get assistant response (prefer the one with most complete response)
    if (span.outputs) {
      if (span.outputs.choices?.[0]?.message?.content) {
        assistantResponse = { content: span.outputs.choices[0].message.content, span };
      } else if (typeof span.outputs === "string") {
        assistantResponse = { content: span.outputs, span };
      } else if (span.outputs.output) {
        assistantResponse = { content: span.outputs.output, span };
      }
    }
  }

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
        {reviewApp?.labeling_schemas?.filter((schema) => schema.type === "FEEDBACK").length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Feedback</h3>
            <div className="space-y-4">
              <Accordion type="single" collapsible className="w-full">
                {reviewApp?.labeling_schemas
                  ?.filter((schema) => schema.type === "FEEDBACK")
                  .map((schema) => {
                    const hasValue =
                      labels[schema.name] !== undefined &&
                      labels[schema.name] !== null &&
                      labels[schema.name] !== "";
                    const isCompleted = hasValue;

                    return (
                      <AccordionItem
                        key={schema.name}
                        value={schema.name}
                        className="border rounded-lg px-4"
                      >
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
                                onValueChange={(value) =>
                                  handleLabelsChange({ ...labels, [schema.name]: value[0] })
                                }
                                min={schema.numeric.min_value}
                                max={schema.numeric.max_value}
                                step={1}
                              />
                            </div>
                          )}

                          {schema.categorical && (
                            <RadioGroup
                              value={labels[schema.name]}
                              onValueChange={(value) =>
                                handleLabelsChange({ ...labels, [schema.name]: value })
                              }
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
                                onChange={(e) =>
                                  handleLabelsChange({ ...labels, [schema.name]: e.target.value })
                                }
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
                                onChange={(e) =>
                                  handleLabelsChange({
                                    ...labels,
                                    [`${schema.name}_comment`]: e.target.value,
                                  })
                                }
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
        {reviewApp?.labeling_schemas?.filter((schema) => schema.type === "EXPECTATION").length >
          0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Expectations</h3>
            <div className="space-y-4">
              <Accordion type="single" collapsible className="w-full">
                {reviewApp?.labeling_schemas
                  ?.filter((schema) => schema.type === "EXPECTATION")
                  .map((schema) => {
                    const hasValue =
                      labels[schema.name] !== undefined &&
                      labels[schema.name] !== null &&
                      labels[schema.name] !== "";
                    const isCompleted = hasValue;

                    return (
                      <AccordionItem
                        key={schema.name}
                        value={schema.name}
                        className="border rounded-lg px-4"
                      >
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
                                onValueChange={(value) =>
                                  handleLabelsChange({ ...labels, [schema.name]: value[0] })
                                }
                                min={schema.numeric.min_value}
                                max={schema.numeric.max_value}
                                step={1}
                              />
                            </div>
                          )}

                          {schema.categorical && (
                            <RadioGroup
                              value={labels[schema.name]}
                              onValueChange={(value) =>
                                handleLabelsChange({ ...labels, [schema.name]: value })
                              }
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
                                onChange={(e) =>
                                  handleLabelsChange({ ...labels, [schema.name]: e.target.value })
                                }
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
                                onChange={(e) =>
                                  handleLabelsChange({
                                    ...labels,
                                    [`${schema.name}_comment`]: e.target.value,
                                  })
                                }
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
                console.error("No trace ID found in item");
                return;
              }

              try {
                // Get the schema names that are relevant to this review app
                const relevantSchemaNames = new Set(
                  reviewApp?.labeling_schemas?.map((schema) => schema.name) || []
                );

                // Convert each label to MLflow assessment, but ONLY for relevant schemas
                const apiLabels = convertLabelsToApiFormat(labels);

                // Track success count for feedback
                let successCount = 0;
                let totalCount = 0;

                // Log all assessments in parallel (only relevant ones)
                const assessmentPromises = Object.entries(apiLabels).map(
                  async ([schemaName, labelData]) => {
                    // Only process assessments that belong to this review app's schemas
                    if (!relevantSchemaNames.has(schemaName)) {
                      console.log(
                        `[SUBMIT] Skipping assessment '${schemaName}' - not relevant to current review app schemas`
                      );
                      return;
                    }

                    // Save if there's either a value OR a rationale
                    if (
                      (labelData.value !== undefined &&
                        labelData.value !== null &&
                        labelData.value !== "") ||
                      (labelData.rationale && labelData.rationale !== "")
                    ) {
                      totalCount++;
                      // Find the schema to determine if it's FEEDBACK or EXPECTATION
                      const schema = reviewApp?.labeling_schemas?.find(
                        (s) => s.name === schemaName
                      );
                      const schemaType = schema?.type || "FEEDBACK";

                      try {
                        if (schemaType === "FEEDBACK") {
                          // Log as feedback using React Query mutation
                          await logFeedbackMutation.mutateAsync({
                            traceId,
                            feedbackKey: schemaName,
                            feedbackValue: labelData.value,
                            rationale: labelData.rationale,
                          });
                          successCount++;
                        } else {
                          // Log as expectation using React Query mutation
                          await logExpectationMutation.mutateAsync({
                            traceId,
                            expectationKey: schemaName,
                            expectationValue: labelData.value,
                            rationale: labelData.rationale,
                          });
                          successCount++;
                        }
                      } catch (error) {
                        // Individual assessment failed, but continue with others
                        console.error(`Failed to log assessment for ${schemaName}:`, error);
                      }
                    }
                  }
                );

                // Wait for all assessments to be logged
                await Promise.all(assessmentPromises);

                // Show appropriate feedback based on success
                if (successCount === totalCount && totalCount > 0) {
                  toast.success("All feedback saved successfully");
                } else if (successCount > 0) {
                  toast.warning(`Saved ${successCount} of ${totalCount} feedback items`);
                } else if (totalCount > 0) {
                  toast.error("Failed to save feedback. Please try again.");
                }

                // Mark item as completed (without labels)
                await onUpdateItem(item.item_id, { state: "COMPLETED" });

                // Move to next item
                if (currentIndex < totalItems - 1) {
                  onNavigateToIndex(currentIndex + 1);
                }
              } catch (error) {
                console.error("Failed to submit assessments:", error);
                toast.error("An unexpected error occurred. Moving to next item.");
                // Still mark as completed even if some assessments failed
                await onUpdateItem(item.item_id, { state: "COMPLETED" });
                if (currentIndex < totalItems - 1) {
                  onNavigateToIndex(currentIndex + 1);
                }
              }
            }}
            disabled={
              isSubmitting ||
              Object.keys(labels).length === 0 ||
              logFeedbackMutation.isPending ||
              logExpectationMutation.isPending
            }
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Submit & Next
          </Button>
        </div>
      </div>
    </div>
  );
}
