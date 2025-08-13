import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, CheckCircle, XCircle, User, Bot, Loader2, Check } from "lucide-react";
import { ItemRendererProps } from "@/types/renderers";
import { SavingStateProvider, useSavingState } from "../contexts/SavingStateContext";
import { LabelSchemaForm } from "./schemas/LabelSchemaForm";
import { ChatMessage } from "./schemas/ChatMessage";

interface NavigationButtonsProps {
  onSkip: () => Promise<void>;
  onSubmit: () => Promise<void>;
  isSubmitting: boolean;
  hasAssessments: boolean;
}

function NavigationButtons({ onSkip, onSubmit, isSubmitting, hasAssessments }: NavigationButtonsProps) {
  const { isSaving, lastSavedAt } = useSavingState();
  
  // Show saving status
  const showSaving = isSaving;
  const showSaved = !isSaving && lastSavedAt && Date.now() - lastSavedAt.getTime() < 3000; // Show "Saved" for 3 seconds

  return (
    <div className="flex items-center gap-4">
      {/* Saving status indicator */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-[80px]">
        {showSaving && (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Saving...
          </>
        )}
        {showSaved && (
          <>
            <Check className="h-3 w-3 text-green-600" />
            <span className="text-green-600">Saved</span>
          </>
        )}
      </div>
      
      <Button
        variant="outline"
        onClick={onSkip}
        disabled={isSubmitting}
      >
        <XCircle className="h-4 w-4 mr-2" />
        Skip
      </Button>
      <Button
        variant="primary"
        onClick={onSubmit}
        disabled={isSubmitting || !hasAssessments}
      >
        <CheckCircle className="h-4 w-4 mr-2" />
        Submit & Next
      </Button>
    </div>
  );
}

function DefaultItemRendererContent({
  item,
  traceData,
  reviewApp,
  session,
  currentIndex,
  totalItems,
  assessments,
  onUpdateItem,
  onNavigateToIndex,
  isSubmitting,
  schemaAssessments,
  extractedConversation,
}: ItemRendererProps) {
  // Use provided data or minimal defaults
  const traceId = extractedConversation?.traceId || item?.source?.trace_id || "";
  
  // Just use what's passed in - no filtering here!
  const feedbackSchemas = schemaAssessments?.feedback || [];
  const expectationSchemas = schemaAssessments?.expectations || [];
  
  // Use extracted conversation or fallback
  let userRequest = extractedConversation?.userRequest;
  let assistantResponse = extractedConversation?.assistantResponse;
  
  if (!extractedConversation) {
    // Minimal fallback - just grab first user/assistant messages
    const spans = traceData?.spans || [];
    
    for (const span of spans) {
      if (!userRequest && span.inputs) {
        if (typeof span.inputs === "string") {
          userRequest = { content: span.inputs };
        } else if ((span.inputs as any)?.messages?.[0]?.content) {
          userRequest = { content: (span.inputs as any).messages[0].content };
        }
      }
      
      if (!assistantResponse && span.outputs) {
        if (typeof span.outputs === "string") {
          assistantResponse = { content: span.outputs };
        } else if ((span.outputs as any)?.choices?.[0]?.message?.content) {
          assistantResponse = { content: (span.outputs as any).choices[0].message.content };
        }
      }
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-24">
      {/* Left column: Conversation */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Conversation</h3>

        <div className="space-y-4">
          {/* User Request */}
          {userRequest && (
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm mb-1">User</div>
                <ChatMessage content={userRequest.content} />
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
                <ChatMessage content={assistantResponse.content} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right column: Separated Feedback and Expectations */}
      <div className="space-y-6">
        {/* Feedback schemas */}
        {feedbackSchemas.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Feedback</h3>
            <LabelSchemaForm
              schemas={feedbackSchemas.map(item => item.schema)}
              assessments={new Map(feedbackSchemas.filter(item => item.assessment).map(item => [item.schema.name, item.assessment!]))}
              traceId={traceId}
              readOnly={false}
              reviewAppId={reviewApp.review_app_id}
              sessionId={session.labeling_session_id}
            />
          </div>
        )}

        {/* Expectation schemas */}
        {expectationSchemas.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Expectations</h3>
            <LabelSchemaForm
              schemas={expectationSchemas.map(item => item.schema)}
              assessments={new Map(expectationSchemas.filter(item => item.assessment).map(item => [item.schema.name, item.assessment!]))}
              traceId={traceId}
              readOnly={false}
              reviewAppId={reviewApp.review_app_id}
              sessionId={session.labeling_session_id}
            />
          </div>
        )}
      </div>

      {/* Actions - Pinned to bottom of screen */}
      <div className="col-span-1 lg:col-span-2 fixed bottom-0 left-0 right-0 bg-background border-t p-4">
        <div className="container mx-auto flex items-center justify-between">
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

          <NavigationButtons
            onSkip={async () => {
              // Mark as skipped and move to next
              await onUpdateItem(item.item_id, { state: "SKIPPED" });
              if (currentIndex < totalItems - 1) {
                onNavigateToIndex(currentIndex + 1);
              }
            }}
            onSubmit={async () => {
              // Assessments are already saved via auto-save
              // Just mark as completed and move to next
              await onUpdateItem(item.item_id, { state: "COMPLETED" });
              if (currentIndex < totalItems - 1) {
                onNavigateToIndex(currentIndex + 1);
              }
            }}
            isSubmitting={isSubmitting}
            hasAssessments={assessments.size > 0}
          />
        </div>
      </div>
    </div>
  );
}

export function DefaultItemRenderer(props: ItemRendererProps) {
  return (
    <SavingStateProvider>
      <DefaultItemRendererContent {...props} />
    </SavingStateProvider>
  );
}
