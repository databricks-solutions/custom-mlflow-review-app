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
  ArrowLeft,
  CheckCircle,
  XCircle,
  Check,
  Circle,
  User,
  Bot,
} from "lucide-react";
import { ItemRendererProps } from "@/types/renderers";
import { Assessment } from "@/types/assessment";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { toast } from "sonner";
import { useLogFeedbackMutation, useLogExpectationMutation } from "@/hooks/shared-hooks";
import { alignSchemaToAssessment } from "@/utils/assessment-utils";

// Constants for span type filtering
const CONVERSATIONAL_SPAN_TYPES = ["CHAT_MODEL", "TOOL", "AGENT", "LLM", "USER", "ASSISTANT"];

export function DefaultItemRenderer({
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
  // Auto-save refs
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedLabelsRef = useRef<string>("");
  const previousLabelsRef = useRef<Record<string, any>>({});

  // React Query mutations for logging assessments
  const logFeedbackMutation = useLogFeedbackMutation();
  const logExpectationMutation = useLogExpectationMutation();

  // Helper function to convert flat labels to API format
  const convertLabelsToApiFormat = (flatLabels: Record<string, any>) => {
    const apiLabels: Record<string, any> = {};

    // Convert flat structure to nested structure expected by API
    Object.keys(flatLabels).forEach((key) => {
      if (key.endsWith("_comment")) {
        // Skip comment fields - they'll be handled with their parent
        return;
      }

      const commentKey = `${key}_comment`;
      const value = flatLabels[key];
      const rationale = flatLabels[commentKey];

      // Save if there's either a value OR a rationale (not both required)
      if (
        (value !== undefined && value !== null && value !== "") ||
        (rationale && rationale !== "")
      ) {
        apiLabels[key] = {
          value: value || null, // Use null for empty values when only rationale exists
          ...(rationale ? { rationale: rationale } : {}),
        };
      }
    });

    return apiLabels;
  };

  // Auto-save functionality - save to MLflow when labels change
  const handleLabelsChange = useCallback(
    async (newLabels: Record<string, any>) => {
      onLabelsChange(newLabels);

      // Clear any existing timeout to debounce the save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Set a new timeout to save after 2 seconds of no changes
      saveTimeoutRef.current = setTimeout(async () => {
        try {
          console.log("[AUTO-SAVE] Starting auto-save for labels:", newLabels);

          // Get trace ID from item
          const traceId = item.source?.trace_id;
          if (!traceId) {
            console.error("[AUTO-SAVE] No trace ID found in item");
            return;
          }

          // Get the schema names that are relevant to this review app
          const relevantSchemaNames = new Set(
            reviewApp?.labeling_schemas?.map((schema) => schema.name) || []
          );

          // Convert labels to API format and save each assessment, but ONLY for relevant schemas
          const apiLabels = convertLabelsToApiFormat(newLabels);
          let savedCount = 0;

          for (const [schemaName, labelData] of Object.entries(apiLabels)) {
            // Only save assessments that belong to this review app's schemas
            if (!relevantSchemaNames.has(schemaName)) {
              console.log(
                `[AUTO-SAVE] Skipping assessment '${schemaName}' - not relevant to current review app schemas`
              );
              continue;
            }

            // Save if there's either a value OR a rationale
            if (
              (labelData.value !== undefined &&
                labelData.value !== null &&
                labelData.value !== "") ||
              (labelData.rationale && labelData.rationale !== "")
            ) {
              try {
                // Find the schema to determine if it's FEEDBACK or EXPECTATION
                const schema = reviewApp?.labeling_schemas?.find((s) => s.name === schemaName);
                const schemaType = schema?.type || "FEEDBACK";

                if (schemaType === "FEEDBACK") {
                  await logFeedbackMutation.mutateAsync({
                    traceId,
                    feedbackKey: schemaName,
                    feedbackValue: labelData.value,
                    rationale: labelData.rationale,
                  });
                } else {
                  await logExpectationMutation.mutateAsync({
                    traceId,
                    expectationKey: schemaName,
                    expectationValue: labelData.value,
                    rationale: labelData.rationale,
                  });
                }
                savedCount++;
                console.log(
                  `[AUTO-SAVE] Saved ${schemaName}: ${labelData.value || "rationale-only"} with rationale: ${labelData.rationale || "none"}`
                );
              } catch (error) {
                console.error(`[AUTO-SAVE] Failed to save ${schemaName}:`, error);
              }
            }
          }

          if (savedCount > 0) {
            console.log(`[AUTO-SAVE] Successfully auto-saved ${savedCount} assessments`);
            // Show subtle feedback that auto-save worked
            toast.success(`Auto-saved ${savedCount} assessment${savedCount > 1 ? "s" : ""}`, {
              duration: 2000,
            });
          }
        } catch (error) {
          console.error("[AUTO-SAVE] Auto-save failed:", error);
        }
      }, 2000); // Auto-save after 2 seconds of no changes
    },
    [
      onLabelsChange,
      item.source?.trace_id,
      reviewApp?.labeling_schemas,
      logFeedbackMutation,
      logExpectationMutation,
      convertLabelsToApiFormat,
    ]
  );

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);


  // Load existing assessments from trace data when item changes
  useEffect(() => {
    const loadExistingLabels = () => {
      console.log(
        "DEBUG: Loading assessments for schemas:",
        reviewApp?.labeling_schemas?.map((s) => s.name)
      );
      console.log(
        "DEBUG: Available assessments:",
        traceData?.info?.assessments?.map((a) => a.name)
      );
      console.log("DEBUG: Full assessments data:", traceData?.info?.assessments);

      // Debug each assessment individually to see their structure
      traceData?.info?.assessments?.forEach((assessment: any, index: number) => {
        console.log(`DEBUG: Assessment ${index}:`, {
          name: assessment.name,
          value: assessment.value,
          rationale: assessment.rationale,
          comment: assessment.comment,
          fullObject: assessment,
        });
      });

      if (!traceData?.info?.assessments || !reviewApp?.labeling_schemas) {
        console.log("No assessments or schemas available");
        onLabelsChange({});
        lastSavedLabelsRef.current = "";
        return;
      }

      const flatLabels: Record<string, any> = {};
      const schemaNames = reviewApp.labeling_schemas.map((s) => s.name);

      // Process all assessments and match them to schema names
      const assessments: Assessment[] = traceData.info.assessments;

      // Group assessments by name and prioritize those with rationale
      const assessmentsByName: Record<string, Assessment[]> = {};
      assessments.forEach((assessment) => {
        if (!assessmentsByName[assessment.name]) {
          assessmentsByName[assessment.name] = [];
        }
        assessmentsByName[assessment.name].push(assessment);
      });

      // For each schema, find the best assessment (prioritize those with rationale)
      Object.entries(assessmentsByName).forEach(([assessmentName, assessmentList]) => {
        console.log(
          `DEBUG: Processing assessment group ${assessmentName} with ${assessmentList.length} entries`
        );

        // Check if this assessment matches a schema name directly
        if (schemaNames.includes(assessmentName)) {
          console.log(`DEBUG: Schema match found for ${assessmentName}`);

          // Sort assessments to prioritize those with rationale
          const sortedAssessments = assessmentList.sort((a, b) => {
            const aHasRationale = !!a.rationale;
            const bHasRationale = !!b.rationale;

            // Prioritize assessments with rationale
            if (aHasRationale && !bHasRationale) return -1;
            if (!aHasRationale && bHasRationale) return 1;
            return 0; // Keep original order if both have or don't have rationale
          });

          // Use the best assessment (first after sorting)
          const bestAssessment = sortedAssessments[0];
          console.log(`DEBUG: Using assessment for ${assessmentName}:`, bestAssessment);

          // Set the assessment value
          if (bestAssessment.value !== undefined && bestAssessment.value !== null) {
            flatLabels[assessmentName] = bestAssessment.value;
            console.log(`Found value for ${assessmentName}:`, bestAssessment.value);
          }

          // Set the rationale (check metadata.rationale due to MLflow bug)
          const rationale = bestAssessment.metadata?.rationale || bestAssessment.rationale;
          if (rationale && rationale !== "") {
            flatLabels[`${assessmentName}_comment`] = rationale;
            console.log(`Found rationale for ${assessmentName}:`, rationale);
          }
        } else {
          console.log(
            `DEBUG: No schema match for assessment ${assessmentName}, available schemas:`,
            schemaNames
          );
        }
      });

      // Update the form with existing labels
      if (Object.keys(flatLabels).length > 0) {
        console.log("Populating form with assessments:", flatLabels);
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
