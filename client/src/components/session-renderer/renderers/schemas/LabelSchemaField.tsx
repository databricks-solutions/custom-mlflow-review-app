import React, { useState, useEffect, useCallback, useRef } from "react";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { CheckCircle, Circle } from "lucide-react";
import { Assessment, LabelingSchema, JsonValue } from "@/types/renderers";
import { useSavingState } from "../../contexts/SavingStateContext";
import {
  useLogFeedbackMutation,
  useLogExpectationMutation,
  useUpdateFeedbackMutation,
  useUpdateExpectationMutation,
  useCurrentUser,
} from "@/hooks/api-hooks";

interface LabelSchemaFieldProps {
  schema: LabelingSchema;
  assessment?: Assessment;
  traceId: string;
  readOnly?: boolean;
}

export function LabelSchemaField({
  schema,
  assessment,
  traceId,
  readOnly = false,
}: LabelSchemaFieldProps) {
  // Local state for immediate UI updates
  const [localValue, setLocalValue] = useState<JsonValue>(assessment?.value || "");
  const [localRationale, setLocalRationale] = useState<string>(assessment?.rationale || "");
  const [localAssessmentId, setLocalAssessmentId] = useState<string | undefined>(
    assessment?.assessment_id
  );

  // Get current user
  const { data: currentUser } = useCurrentUser();
  const currentUsername = currentUser?.emails?.[0] || currentUser?.userName || "unknown";

  // Saving state
  const { setSaving, setLastSaved } = useSavingState();

  // Mutations
  const logFeedbackMutation = useLogFeedbackMutation();
  const logExpectationMutation = useLogExpectationMutation();
  const updateFeedbackMutation = useUpdateFeedbackMutation();
  const updateExpectationMutation = useUpdateExpectationMutation();

  // Debounce timer ref
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update local state when assessment prop changes
  useEffect(() => {
    setLocalValue(assessment?.value || "");
    setLocalRationale(assessment?.rationale || "");
    // IMPORTANT: Preserve the assessment_id from existing assessments
    setLocalAssessmentId(assessment?.assessment_id || null);
  }, [assessment]);

  // Handle the actual save logic
  const performSave = useCallback(
    async (value: JsonValue, rationale: string) => {
      // Skip if empty
      if (
        (value === undefined || value === null || value === "") &&
        (!rationale || rationale === "")
      ) {
        return;
      }

      setSaving(true);
      try {
        const schemaType = schema.type || "FEEDBACK";
        let result: LogFeedbackResponse | LogExpectationResponse | UpdateFeedbackResponse | UpdateExpectationResponse | undefined;

        // Simple logic: if we have an assessment_id, update; otherwise create
        const hasExistingAssessment = !!localAssessmentId;

        if (schemaType === "FEEDBACK") {
          if (hasExistingAssessment) {
            // UPDATE existing feedback
            result = await updateFeedbackMutation.mutateAsync({
              traceId,
              assessmentId: localAssessmentId,
              value: value as string | number | boolean | string[] | Record<string, unknown>,
              rationale: rationale || undefined,
            });
          } else {
            // CREATE new feedback
            result = await logFeedbackMutation.mutateAsync({
              traceId,
              name: schema.name,
              value: value as string | number | boolean | string[] | Record<string, unknown>,
              rationale: rationale || undefined,
            });
          }
        } else {
          // EXPECTATION type
          if (hasExistingAssessment) {
            // UPDATE existing expectation
            result = await updateExpectationMutation.mutateAsync({
              traceId,
              assessmentId: localAssessmentId,
              value: value as string | number | boolean | string[] | Record<string, unknown>,
              rationale: rationale || undefined,
            });
          } else {
            // CREATE new expectation
            result = await logExpectationMutation.mutateAsync({
              traceId,
              name: schema.name,
              value: value as string | number | boolean | string[] | Record<string, unknown>,
              rationale: rationale || undefined,
            });
          }
        }

        // Update local assessment ID if we created a new one
        if (result && 'assessment_id' in result && result.assessment_id && !localAssessmentId) {
          setLocalAssessmentId(result.assessment_id);
        }

        setLastSaved();
      } catch (error) {
        setSaving(false);
        console.error(`Failed to save ${schema.title || schema.name}:`, error);
      }
    },
    [
      schema,
      traceId,
      localAssessmentId,
      assessment,
      currentUsername,
      setSaving,
      setLastSaved,
      logFeedbackMutation,
      logExpectationMutation,
      updateFeedbackMutation,
      updateExpectationMutation,
    ]
  );

  // Trigger save with debounce
  const triggerSave = useCallback(
    (value: JsonValue, rationale: string) => {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Set new timeout for auto-save
      saveTimeoutRef.current = setTimeout(() => {
        performSave(value, rationale);
      }, 500); // 500ms debounce
    },
    [performSave]
  );

  // Handle value change
  const handleValueChange = (newValue: JsonValue) => {
    setLocalValue(newValue);
    triggerSave(newValue, localRationale);
  };

  // Handle rationale change
  const handleRationaleChange = (newRationale: string) => {
    setLocalRationale(newRationale);
    triggerSave(localValue, newRationale);
  };

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Check if field has value
  const hasValue = localValue !== undefined && localValue !== null && localValue !== "";
  const isCompleted = hasValue;

  return (
    <AccordionItem value={schema.name} className="border rounded-lg px-4">
      <AccordionTrigger className="hover:no-underline">
        <div className="flex items-center gap-2">
          {isCompleted ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <Circle className="h-4 w-4 text-gray-400" />
          )}
          <span className="font-medium">{schema.title || schema.name}</span>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pt-4">
        {schema.instruction && (
          <p className="text-sm text-muted-foreground">{schema.instruction}</p>
        )}

        {/* Numeric rating */}
        {schema.numeric && (
          <div className="space-y-2">
            <Label>Rating</Label>
            <Slider
              value={[Number(localValue) || schema.numeric.min_value]}
              onValueChange={([value]) => handleValueChange(value)}
              min={schema.numeric.min_value}
              max={schema.numeric.max_value}
              step={1}
              disabled={readOnly}
              className="py-4"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{schema.numeric.min_value}</span>
              <span className="font-medium text-foreground">
                {Number(localValue) || schema.numeric.min_value}
              </span>
              <span>{schema.numeric.max_value}</span>
            </div>
          </div>
        )}

        {/* Categorical options */}
        {schema.categorical && (
          <RadioGroup
            value={String(localValue)}
            onValueChange={handleValueChange}
            disabled={readOnly}
          >
            {schema.categorical.options?.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <RadioGroupItem value={option} id={`${schema.name}-${option}`} />
                <Label htmlFor={`${schema.name}-${option}`}>{option}</Label>
              </div>
            ))}
          </RadioGroup>
        )}

        {/* Text input */}
        {schema.text && (
          <div className="space-y-2">
            <Label htmlFor={schema.name}>Response</Label>
            <Textarea
              id={schema.name}
              value={String(localValue)}
              onChange={(e) => handleValueChange(e.target.value)}
              placeholder="Enter your response..."
              rows={4}
              disabled={readOnly}
            />
          </div>
        )}

        {/* Rationale/Comments */}
        {schema.enable_comment && (
          <div className="space-y-2 pt-2 border-t">
            <Label htmlFor={`${schema.name}_rationale`}>Comments</Label>
            <Textarea
              id={`${schema.name}_rationale`}
              value={localRationale}
              onChange={(e) => handleRationaleChange(e.target.value)}
              placeholder="Add your reasoning or additional feedback..."
              rows={2}
              disabled={readOnly}
            />
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
