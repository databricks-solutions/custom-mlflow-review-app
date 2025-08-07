import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Clock,
  MessageSquare,
  Bot,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
  Wrench,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  User,
  Copy,
  Search,
  Filter,
  MoreHorizontal,
  Play,
  Pause,
} from "lucide-react";
import {
  ChatBubble,
  ChatBubbleAvatar,
  ChatBubbleMessage,
  ChatBubbleTimestamp,
  ChatMessageList,
} from "@/components/ui/chat";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useTrace, useTraceMetadata } from "@/hooks/api-hooks";

interface TraceExplorerProps {
  traceId: string;
  experimentId?: string;
  databricksHost?: string;
}

interface SpanData {
  name: string;
  span_type: string;
  start_time_ms: number;
  end_time_ms: number;
  status: string;
  attributes: Record<string, any>;
  events?: Array<{
    name: string;
    timestamp: number;
    attributes: Record<string, any>;
  }>;
}

interface TraceData {
  info: {
    trace_id: string;
    request_time: string;
    execution_duration: string;
    state: string;
  };
  data: {
    spans: SpanData[];
  };
}

export const TraceExplorer: React.FC<TraceExplorerProps> = ({
  traceId,
  experimentId,
  databricksHost,
}) => {
  const {
    data: traceData,
    isLoading,
    error,
  } = useTrace(traceId, !!traceId);

  // Construct MLflow trace URL
  const buildMLflowTraceUrl = () => {
    if (!experimentId || !databricksHost) return null;
    return `https://${databricksHost}/ml/experiments/${experimentId}/traces?selectedEvaluationId=${traceId}`;
  };

  const mlflowUrl = buildMLflowTraceUrl();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (error || !traceData) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <p className="text-muted-foreground">Failed to load trace data</p>
          <p className="text-sm text-muted-foreground mt-1">Trace ID: {traceId}</p>
          {error && (
            <p className="text-xs text-muted-foreground mt-2">
              Error: {(error as any)?.message || 'Unknown error'}
            </p>
          )}
          <p className="text-xs text-muted-foreground mt-4">
            This trace may not exist or may have been deleted.
          </p>
        </CardContent>
      </Card>
    );
  }

  return <TraceViewer trace={traceData} mlflowUrl={mlflowUrl} />;
};

const TraceViewer: React.FC<{ trace: TraceData; mlflowUrl?: string | null }> = ({
  trace,
  mlflowUrl,
}) => {
  const [activeTab, setActiveTab] = useState("summary");
  const [renderMode, setRenderMode] = useState("default"); // default is markdown
  const [isInputsExpanded, setIsInputsExpanded] = useState(false);
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());

  const spans = trace.data?.spans || [];
  const rootSpan = spans[0];
  const sortedSpans = [...spans].sort((a, b) => a.start_time_ms - b.start_time_ms);
  
  // Filter spans for Summary view to only show TOOL and LLM spans
  const isToolOrLLMSpan = (span: SpanData): boolean => {
    const spanType = span.span_type?.toUpperCase();
    const mlflowSpanType = span.attributes?.["mlflow.spanType"]?.toUpperCase();
    
    return (
      spanType === "TOOL" || 
      spanType === "LLM" || 
      spanType === "CHAT" ||
      mlflowSpanType === "TOOL" || 
      mlflowSpanType === "LLM" ||
      mlflowSpanType === "CHAT"
    );
  };
  
  const filteredSpansForSummary = sortedSpans.filter(isToolOrLLMSpan);

  // Parse conversation from spans
  const conversation = parseConversationFromSpans(sortedSpans);

  const toggleSpan = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const formatDuration = (startTime: number, endTime: number) => {
    if (!startTime || !endTime || isNaN(startTime) || isNaN(endTime)) {
      return "0ms";
    }
    const duration = endTime - startTime;
    if (isNaN(duration) || duration < 0) {
      return "0ms";
    }
    if (duration < 1000) return `${Math.round(duration)}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const getSpanIcon = (span: SpanData) => {
    const type = span.span_type?.toLowerCase() || "";
    const mlflowType = span.attributes?.["mlflow.spanType"]?.toLowerCase() || "";
    const name = span.name?.toLowerCase() || "";
    
    if (type === "tool" || mlflowType === "tool" || name.includes("tool")) {
      return <Wrench className="h-4 w-4 text-red-600" />;
    } else if (
      type === "llm" ||
      type === "chat" ||
      mlflowType === "llm" ||
      mlflowType === "chat" ||
      name.includes("chat") ||
      name.includes("databricks")
    ) {
      return <Bot className="h-4 w-4 text-blue-600" />;
    }
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const getSpanName = (span: SpanData) => {
    return span.name || "Unknown";
  };

  const parseSpanData = (span: SpanData) => {
    let input = "";
    let output = "";

    try {
      const inputAttr = span.attributes?.["mlflow.spanInputs"];
      const outputAttr = span.attributes?.["mlflow.spanOutputs"];

      if (inputAttr) {
        const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;
        input = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }

      if (outputAttr) {
        const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;
        output = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }
    } catch (e) {
      // Ignore parsing errors
    }

    return { input, output };
  };

  // Calculate total duration
  const totalDuration =
    trace.info?.execution_duration ||
    (rootSpan ? `${rootSpan.end_time_ms - rootSpan.start_time_ms}ms` : "Unknown");

  // Parse root span inputs for the expandable section
  const parseRootInputs = () => {
    if (!rootSpan?.attributes?.["mlflow.spanInputs"]) return null;
    try {
      return JSON.parse(rootSpan.attributes["mlflow.spanInputs"]);
    } catch {
      return rootSpan.attributes["mlflow.spanInputs"];
    }
  };

  const rootInputs = parseRootInputs();

  return (
    <div className="space-y-4">
      {/* Header with MLflow link */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Trace {trace.info.trace_id}</h2>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>Duration: {totalDuration}</span>
            <span>Status: {trace.info.state}</span>
          </div>
        </div>
        {mlflowUrl && (
          <a
            href={mlflowUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            View in MLflow
          </a>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="details">Details & Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4">
          {/* Conversation Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Conversation</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Render mode:</span>
                <Button
                  variant={renderMode === "default" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setRenderMode("default")}
                >
                  Default
                </Button>
                <Button
                  variant={renderMode === "json" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setRenderMode("json")}
                >
                  JSON
                </Button>
              </div>
            </div>

            {/* User question */}
            <div className="space-y-4">
              {/* Show initial user message */}
              {conversation.find((item) => item.type === "message" && item.role === "user") && (
                <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm mb-1">User</div>
                    <div className="text-sm">
                      {renderMode === "json" ? (
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(
                            conversation.find(
                              (item) => item.type === "message" && item.role === "user"
                            )?.content,
                            null,
                            2
                          )}
                        </pre>
                      ) : (
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>
                            {
                              conversation.find(
                                (item) => item.type === "message" && item.role === "user"
                              )?.content || ""
                            }
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Show only TOOL and LLM spans in chronological order */}
              <div className="ml-11 space-y-2">
                {filteredSpansForSummary.map((span, index) => {
                  const spanId = `summary-${span.name}-${span.start_time_ms}`;
                  const isExpanded = expandedSpans.has(spanId);
                  const { input, output } = parseSpanData(span);
                  const duration = formatDuration(span.start_time_ms, span.end_time_ms);
                  const spanIcon = getSpanIcon(span);
                  const spanName = getSpanName(span);

                  return (
                    <Collapsible
                      key={spanId}
                      open={isExpanded}
                      onOpenChange={() => toggleSpan(spanId)}
                    >
                      <CollapsibleTrigger className="w-full">
                        <div className="flex items-center justify-between p-3 hover:bg-muted/50 rounded-lg border">
                          <div className="flex items-center gap-3">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            )}
                            {spanIcon}
                            <span className="font-medium text-sm">{spanName}</span>
                            <span className="text-xs text-muted-foreground">was called</span>
                          </div>
                          <div className="text-xs text-muted-foreground">{duration}</div>
                        </div>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="p-4 bg-muted/20 ml-7">
                          {/* Show input if available */}
                          {input && (
                            <div className="mb-4">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-sm font-medium">Inputs</span>
                              </div>
                              <div className="bg-background border rounded-lg p-3">
                                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                                  {input}
                                </pre>
                              </div>
                            </div>
                          )}

                          {/* Show output if available */}
                          {output && (
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-sm font-medium">Outputs</span>
                              </div>
                              <div className="bg-background border rounded-lg p-3">
                                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                                  {output}
                                </pre>
                              </div>
                            </div>
                          )}

                          {!input && !output && (
                            <div className="text-sm text-muted-foreground">
                              No input/output data available for this span
                            </div>
                          )}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  );
                })}
              </div>

              {/* Show final assistant response */}
              {conversation.find(
                (item) => item.type === "message" && item.role === "assistant"
              ) && (
                <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm mb-1">Assistant</div>
                    <div className="text-sm">
                      {renderMode === "json" ? (
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(
                            conversation.find(
                              (item) => item.type === "message" && item.role === "assistant"
                            )?.content,
                            null,
                            2
                          )}
                        </pre>
                      ) : (
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>
                            {
                              conversation.find(
                                (item) => item.type === "message" && item.role === "assistant"
                              )?.content || ""
                            }
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          {/* MLflow-style detailed view */}
          <div className="border rounded-lg overflow-hidden">
            <MLflowStyleTraceView spans={sortedSpans} conversation={conversation} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ToolSpanView: React.FC<{ span: SpanData }> = ({ span }) => {
  const toolName = span.name || "Unknown Tool";
  const duration = span.end_time_ms - span.start_time_ms;

  // Try to extract tool input/output
  let toolInput = "";
  let toolOutput = "";

  try {
    const inputAttr = span.attributes?.["mlflow.spanInputs"];
    const outputAttr = span.attributes?.["mlflow.spanOutputs"];

    if (inputAttr) {
      const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;
      toolInput = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
    }

    if (outputAttr) {
      const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;
      toolOutput = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
    }
  } catch (e) {
    // Ignore parsing errors
  }

  return (
    <div className="border rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wrench className="h-4 w-4" />
          <span className="font-medium">{toolName}</span>
        </div>
        <Badge variant="outline">{duration}ms</Badge>
      </div>

      {toolInput && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">Input:</p>
          <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-24">
            {toolInput.length > 200 ? toolInput.substring(0, 200) + "..." : toolInput}
          </pre>
        </div>
      )}

      {toolOutput && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">Output:</p>
          <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-24">
            {toolOutput.length > 200 ? toolOutput.substring(0, 200) + "..." : toolOutput}
          </pre>
        </div>
      )}
    </div>
  );
};

const SpanTimelineView: React.FC<{ span: SpanData; rootStartTime: number }> = ({
  span,
  rootStartTime,
}) => {
  const relativeStart = span.start_time_ms - rootStartTime;
  const duration = span.end_time_ms - span.start_time_ms;
  const spanType = span.span_type || "UNKNOWN";

  const getSpanIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "llm":
      case "chat":
        return <Bot className="h-3 w-3" />;
      case "tool":
        return <Wrench className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  const getSpanColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "llm":
      case "chat":
        return "bg-blue-100 border-blue-200";
      case "tool":
        return "bg-green-100 border-green-200";
      default:
        return "bg-gray-100 border-gray-200";
    }
  };

  return (
    <div className={`flex items-center gap-3 p-2 rounded border ${getSpanColor(spanType)}`}>
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {getSpanIcon(spanType)}
        <span className="text-sm font-medium truncate">{span.name}</span>
        <Badge variant="outline" className="text-xs">
          {spanType}
        </Badge>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span>+{relativeStart}ms</span>
        <span>{duration}ms</span>
      </div>
    </div>
  );
};

// Helper function to parse conversation from all spans in chronological order
function parseConversationFromSpans(spans: SpanData[]): Array<{
  type: "message" | "tool";
  role?: string;
  content?: string;
  timestamp?: string;
  name?: string;
  input?: string;
  output?: string;
}> {
  const conversation: Array<{
    type: "message" | "tool";
    role?: string;
    content?: string;
    timestamp?: string;
    name?: string;
    input?: string;
    output?: string;
  }> = [];

  // First, add the initial user message from the root span
  const rootSpan = spans[0];
  if (rootSpan) {
    try {
      const inputAttr = rootSpan.attributes?.["mlflow.spanInputs"];
      if (inputAttr) {
        const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;

        if (parsed.messages && Array.isArray(parsed.messages)) {
          // Find the last user message to show as the initial question
          const userMessages = parsed.messages.filter((m: any) => m.role === "user");
          if (userMessages.length > 0) {
            conversation.push({
              type: "message",
              role: "user",
              content: userMessages[userMessages.length - 1].content,
              timestamp: new Date(rootSpan.start_time_ms).toLocaleString(),
            });
          }
        } else if (typeof parsed === "string") {
          conversation.push({
            type: "message",
            role: "user",
            content: parsed,
            timestamp: new Date(rootSpan.start_time_ms).toLocaleString(),
          });
        }
      }
    } catch (e) {
      console.warn("Failed to parse root span input:", e);
    }
  }

  // Then add tool calls in chronological order
  spans.forEach((span) => {
    if (
      span.span_type === "TOOL" ||
      span.name?.toLowerCase().includes("tool") ||
      span.attributes?.["mlflow.spanType"] === "TOOL"
    ) {
      let toolInput = "";
      let toolOutput = "";

      try {
        const inputAttr = span.attributes?.["mlflow.spanInputs"];
        const outputAttr = span.attributes?.["mlflow.spanOutputs"];

        if (inputAttr) {
          const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;
          toolInput = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
        }

        if (outputAttr) {
          const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;
          toolOutput = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
        }
      } catch (e) {
        // Ignore parsing errors
      }

      conversation.push({
        type: "tool",
        name: span.name || "Unknown Tool",
        input: toolInput,
        output: toolOutput,
        timestamp: new Date(span.start_time_ms).toLocaleString(),
      });
    }
  });

  // Finally, add the assistant response from the root span
  if (rootSpan) {
    try {
      const outputAttr = rootSpan.attributes?.["mlflow.spanOutputs"];
      if (outputAttr) {
        const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;

        if (parsed.choices && parsed.choices[0]?.message?.content) {
          conversation.push({
            type: "message",
            role: "assistant",
            content: parsed.choices[0].message.content,
            timestamp: new Date(rootSpan.end_time_ms).toLocaleString(),
          });
        } else if (typeof parsed === "string") {
          conversation.push({
            type: "message",
            role: "assistant",
            content: parsed,
            timestamp: new Date(rootSpan.end_time_ms).toLocaleString(),
          });
        }
      }
    } catch (e) {
      console.warn("Failed to parse root span output:", e);
    }
  }

  return conversation;
}

// MLflow-style trace view component with hierarchical spans and tabbed content
const MLflowStyleTraceView: React.FC<{ 
  spans: SpanData[]; 
  conversation: Array<{
    type: "message" | "tool";
    role?: string;
    content?: string;
    timestamp?: string;
    name?: string;
    input?: string;
    output?: string;
  }>;
}> = ({ spans, conversation }) => {
  const [selectedSpan, setSelectedSpan] = useState<SpanData | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState("");
  const [activeContentTab, setActiveContentTab] = useState("chat");

  // Build span hierarchy
  const buildSpanHierarchy = (spans: SpanData[]) => {
    const spanMap = new Map<string, SpanData & { children: SpanData[] }>();
    const rootSpans: (SpanData & { children: SpanData[] })[] = [];

    // First pass: create map with children arrays
    spans.forEach(span => {
      const spanId = span.attributes?.['mlflow.span_id'] || `${span.name}-${span.start_time_ms}`;
      spanMap.set(spanId, { ...span, children: [] });
    });

    // Second pass: build hierarchy
    spans.forEach(span => {
      const spanId = span.attributes?.['mlflow.span_id'] || `${span.name}-${span.start_time_ms}`;
      const parentId = span.attributes?.['mlflow.parent_id'];
      const spanWithChildren = spanMap.get(spanId)!;

      if (parentId && spanMap.has(parentId)) {
        spanMap.get(parentId)!.children.push(spanWithChildren);
      } else {
        rootSpans.push(spanWithChildren);
      }
    });

    return rootSpans;
  };

  const hierarchicalSpans = buildSpanHierarchy(spans);

  const toggleSpan = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const formatDuration = (startTime: number, endTime: number) => {
    if (!startTime || !endTime || isNaN(startTime) || isNaN(endTime)) {
      return "0ms";
    }
    const duration = endTime - startTime;
    if (isNaN(duration) || duration < 0) {
      return "0ms";
    }
    if (duration < 1000) return `${Math.round(duration)}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const getSpanIcon = (span: SpanData) => {
    const type = span.span_type?.toLowerCase() || "";
    const mlflowType = span.attributes?.["mlflow.spanType"]?.toLowerCase() || "";
    const name = span.name?.toLowerCase() || "";
    
    if (type === "tool" || mlflowType === "tool" || name.includes("tool")) {
      return <Wrench className="h-4 w-4 text-red-600" />;
    } else if (type === "llm" || type === "chat" || mlflowType === "llm" || mlflowType === "chat") {
      return <Bot className="h-4 w-4 text-blue-600" />;
    }
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const renderSpanItem = (span: SpanData & { children: SpanData[] }, depth: number = 0) => {
    const spanId = span.attributes?.['mlflow.span_id'] || `${span.name}-${span.start_time_ms}`;
    const isExpanded = expandedSpans.has(spanId);
    const isSelected = selectedSpan?.name === span.name && selectedSpan?.start_time_ms === span.start_time_ms;
    const duration = formatDuration(span.start_time_ms, span.end_time_ms);
    const hasChildren = span.children.length > 0;

    return (
      <div key={spanId}>
        <div
          className={`flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 cursor-pointer text-sm ${
            isSelected ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
          }`}
          style={{ paddingLeft: `${8 + depth * 16}px` }}
          onClick={() => setSelectedSpan(span)}
        >
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleSpan(spanId);
              }}
              className="p-0.5 hover:bg-muted rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-3 w-3 text-muted-foreground" />
              )}
            </button>
          ) : (
            <div className="w-4" />
          )}
          {getSpanIcon(span)}
          <span className="font-medium truncate flex-1">{span.name}</span>
          <span className="text-xs text-muted-foreground">{duration}</span>
        </div>
        {hasChildren && isExpanded && (
          <div>
            {span.children.map(child => renderSpanItem(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const getSelectedSpanData = () => {
    if (!selectedSpan) return { input: "", output: "" };
    
    let input = "";
    let output = "";

    try {
      const inputAttr = selectedSpan.attributes?.["mlflow.spanInputs"];
      const outputAttr = selectedSpan.attributes?.["mlflow.spanOutputs"];

      if (inputAttr) {
        const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;
        input = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }

      if (outputAttr) {
        const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;
        output = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }
    } catch (e) {
      // Ignore parsing errors
    }

    return { input, output };
  };

  const selectedSpanData = getSelectedSpanData();

  return (
    <div className="flex h-[600px]">
      {/* Left panel - Span hierarchy */}
      <div className="w-1/3 border-r flex flex-col">
        {/* Search and controls */}
        <div className="p-3 border-b bg-muted/20">
          <div className="flex items-center gap-2 mb-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search spans..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{spans.length} spans</span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="h-6 px-2">
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>

        {/* Span list */}
        <div className="flex-1 overflow-auto">
          {hierarchicalSpans.map(span => renderSpanItem(span))}
        </div>
      </div>

      {/* Right panel - Content tabs */}
      <div className="flex-1 flex flex-col">
        {selectedSpan ? (
          <>
            {/* Selected span header */}
            <div className="p-3 border-b bg-muted/20">
              <div className="flex items-center gap-2 mb-1">
                {getSpanIcon(selectedSpan)}
                <span className="font-medium">{selectedSpan.name}</span>
                <Badge variant="outline" className="text-xs">
                  {selectedSpan.span_type || selectedSpan.attributes?.["mlflow.spanType"] || "UNKNOWN"}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                Duration: {formatDuration(selectedSpan.start_time_ms, selectedSpan.end_time_ms)}
              </div>
            </div>

            {/* Content tabs */}
            <Tabs value={activeContentTab} onValueChange={setActiveContentTab} className="flex-1 flex flex-col overflow-hidden">
              <TabsList className="grid w-full grid-cols-4 flex-shrink-0">
                <TabsTrigger value="chat">Chat</TabsTrigger>
                <TabsTrigger value="inputs">Inputs/Outputs</TabsTrigger>
                <TabsTrigger value="attributes">Attributes</TabsTrigger>
                <TabsTrigger value="events">Events</TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 p-4 overflow-auto">
                {/* Show conversation-style view for this span */}
                <div className="space-y-4">
                  {selectedSpanData.input && (
                    <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm mb-1">Input</div>
                        <div className="text-sm whitespace-pre-wrap">{selectedSpanData.input}</div>
                      </div>
                    </div>
                  )}
                  {selectedSpanData.output && (
                    <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
                      <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm mb-1">Output</div>
                        <div className="text-sm whitespace-pre-wrap">{selectedSpanData.output}</div>
                      </div>
                    </div>
                  )}
                  {!selectedSpanData.input && !selectedSpanData.output && (
                    <div className="text-center text-muted-foreground py-8">
                      No chat data available for this span
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="inputs" className="flex-1 p-4 overflow-auto">
                <div className="space-y-4">
                  {selectedSpanData.input && (
                    <div>
                      <h4 className="font-medium mb-2">Inputs</h4>
                      <div className="bg-muted rounded-lg p-3">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {selectedSpanData.input}
                        </pre>
                      </div>
                    </div>
                  )}
                  {selectedSpanData.output && (
                    <div>
                      <h4 className="font-medium mb-2">Outputs</h4>
                      <div className="bg-muted rounded-lg p-3">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {selectedSpanData.output}
                        </pre>
                      </div>
                    </div>
                  )}
                  {!selectedSpanData.input && !selectedSpanData.output && (
                    <div className="text-center text-muted-foreground py-8">
                      No input/output data available
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="attributes" className="flex-1 p-4 overflow-auto">
                <div className="space-y-2">
                  {selectedSpan.attributes && Object.keys(selectedSpan.attributes).length > 0 ? (
                    Object.entries(selectedSpan.attributes).map(([key, value]) => (
                      <div key={key} className="flex items-start gap-3 p-2 border rounded">
                        <div className="font-mono text-xs text-muted-foreground min-w-0 flex-1">
                          {key}
                        </div>
                        <div className="font-mono text-xs break-all">
                          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      No attributes available
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="events" className="flex-1 p-4 overflow-auto">
                <div className="space-y-2">
                  {selectedSpan.events && selectedSpan.events.length > 0 ? (
                    selectedSpan.events.map((event, index) => (
                      <div key={index} className="p-3 border rounded">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{event.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(event.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {event.attributes && Object.keys(event.attributes).length > 0 && (
                          <div className="text-xs text-muted-foreground">
                            <pre>{JSON.stringify(event.attributes, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      No events available
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Select a span to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Legacy component for MLflow-style trace flow (keeping for backward compatibility)
const TraceFlowView: React.FC<{ spans: SpanData[] }> = ({ spans }) => {
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());

  const toggleSpan = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const formatDuration = (startTime: number, endTime: number) => {
    if (!startTime || !endTime || isNaN(startTime) || isNaN(endTime)) {
      return "0ms";
    }
    const duration = endTime - startTime;
    if (isNaN(duration) || duration < 0) {
      return "0ms";
    }
    if (duration < 1000) return `${Math.round(duration)}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const getSpanIcon = (span: SpanData) => {
    const type = span.span_type?.toLowerCase() || "";
    const mlflowType = span.attributes?.["mlflow.spanType"]?.toLowerCase() || "";
    const name = span.name?.toLowerCase() || "";
    
    if (type === "tool" || mlflowType === "tool" || name.includes("tool")) {
      return <Wrench className="h-4 w-4 text-red-600" />;
    } else if (type === "llm" || type === "chat" || mlflowType === "llm" || mlflowType === "chat") {
      return <Bot className="h-4 w-4 text-blue-600" />;
    }
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const getSpanName = (span: SpanData) => {
    if (span.span_type === "TOOL" || span.name?.toLowerCase().includes("tool")) {
      return span.name || "Tool Call";
    } else if (span.span_type === "LLM" || span.span_type === "CHAT") {
      return "ChatDatabricks";
    }
    return span.name || "Unknown";
  };

  const parseSpanData = (span: SpanData) => {
    let input = "";
    let output = "";

    try {
      const inputAttr = span.attributes?.["mlflow.spanInputs"];
      const outputAttr = span.attributes?.["mlflow.spanOutputs"];

      if (inputAttr) {
        const parsed = typeof inputAttr === "string" ? JSON.parse(inputAttr) : inputAttr;
        input = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }

      if (outputAttr) {
        const parsed = typeof outputAttr === "string" ? JSON.parse(outputAttr) : outputAttr;
        output = typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
      }
    } catch (e) {
      // Ignore parsing errors
    }

    return { input, output };
  };

  return (
    <div>
      {spans.map((span, index) => {
        const spanId = `${span.name}-${span.start_time_ms}`;
        const isExpanded = expandedSpans.has(spanId);
        const { input, output } = parseSpanData(span);
        const duration = formatDuration(span.start_time_ms, span.end_time_ms);

        return (
          <Collapsible key={spanId} open={isExpanded} onOpenChange={() => toggleSpan(spanId)}>
            <CollapsibleTrigger className="w-full">
              <div
                className={`flex items-center justify-between p-3 hover:bg-muted/50 ${
                  index !== spans.length - 1 ? "border-b" : ""
                }`}
              >
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                  {getSpanIcon(span)}
                  <span className="font-medium text-sm">{getSpanName(span)}</span>
                  <span className="text-xs text-muted-foreground">was called</span>
                </div>
                <div className="text-xs text-muted-foreground">{duration}</div>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="p-4 bg-muted/20 border-b">
                {/* Show input if available */}
                {input && (
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium">Inputs</span>
                    </div>
                    <div className="bg-background border rounded-lg p-3">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">{input}</pre>
                    </div>
                  </div>
                )}

                {/* Show output if available */}
                {output && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium">Outputs</span>
                    </div>
                    <div className="bg-background border rounded-lg p-3">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">{output}</pre>
                    </div>
                  </div>
                )}

                {!input && !output && (
                  <div className="text-sm text-muted-foreground">
                    No input/output data available for this span
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
};
