import React from "react";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Wrench,
  User,
  Bot,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { ItemRendererProps } from "@/types/renderers";
import { LabelSchemaForm } from "./schemas/LabelSchemaForm";
import { ChatMessage } from "./schemas/ChatMessage";

export function ToolRenderer({
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
  // State for collapsible tool sections
  const [openTools, setOpenTools] = React.useState<Set<string>>(new Set());

  // Use provided data or minimal defaults
  const traceId = extractedConversation?.traceId || item?.source?.trace_id || "";
  
  // Just use what's passed in - no filtering here!
  const feedbackSchemas = schemaAssessments?.feedback || [];
  const expectationSchemas = schemaAssessments?.expectations || [];

  // Use extracted conversation or fallback
  let userRequest = extractedConversation?.userRequest;
  let assistantResponse = extractedConversation?.assistantResponse;
  
  // Filter for tool spans from all spans
  const allSpans = extractedConversation?.spans || traceData?.spans || [];
  const toolSpans = allSpans.filter(span => 
    span.span_type === "TOOL" || span.type === "TOOL"
  );
  
  if (!extractedConversation) {
    // Minimal fallback - extract user/assistant messages
    for (const span of allSpans) {
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

  const toggleTool = (toolId: string) => {
    setOpenTools((prev) => {
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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-24">
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
                <ChatMessage content={userRequest.content} />
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
                                <ChatMessage content={toolSpan.outputs} />
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
                // Review completed - assessments auto-saved
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
    </div>
  );
}
