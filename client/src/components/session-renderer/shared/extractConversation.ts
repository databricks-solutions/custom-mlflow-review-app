/**
 * Utility to extract and deduplicate conversation data from MLflow trace spans
 * Shared by all renderers to ensure consistent conversation extraction
 */

export interface ConversationData {
  userRequest: { content: string } | null;
  assistantResponse: { content: string } | null;
  toolSpans: any[];
}

/**
 * Get the span type from a span object
 */
function getSpanType(span: any): string {
  return span.span_type || span.attributes?.["mlflow.spanType"] || "UNKNOWN";
}

/**
 * Extract user message from a span for deduplication
 */
function getUserMessage(span: any): string | null {
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
}

/**
 * Extract conversation data from trace spans
 * Handles deduplication and separation of user/assistant/tool messages
 */
export function extractConversation(spans: any[]): ConversationData {
  // Filter for conversational spans
  const conversationalSpans = spans.filter((span) => {
    const spanType = getSpanType(span);
    return ["CHAT_MODEL", "TOOL", "AGENT", "LLM", "USER", "ASSISTANT"].includes(spanType);
  });

  // Deduplicate conversation spans by user message content
  const seenUserMessages = new Set<string>();
  const deduplicatedSpans = conversationalSpans.filter((span) => {
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

  // Separate spans by type
  const conversationSpans = deduplicatedSpans.filter((span) => getSpanType(span) !== "TOOL");
  const toolSpans = deduplicatedSpans.filter((span) => getSpanType(span) === "TOOL");

  // Extract user request and assistant response
  let userRequest = null;
  let assistantResponse = null;

  for (const span of conversationSpans) {
    // Try to get user message
    if (!userRequest) {
      if (span.attributes?.["mlflow.chat.messages"]) {
        const messages = span.attributes["mlflow.chat.messages"];
        const userMessage = messages.find((msg: any) => msg.role === "user");
        if (userMessage) {
          userRequest = { content: userMessage.content };
        }
      } else if (span.inputs?.messages) {
        const userMessage = span.inputs.messages.find((msg: any) => msg.role === "user");
        if (userMessage) {
          userRequest = { content: userMessage.content };
        }
      } else if (span.inputs && typeof span.inputs === "string") {
        userRequest = { content: span.inputs };
      }
    }

    // Try to get assistant response
    if (span.outputs) {
      if (span.outputs.choices?.[0]?.message?.content) {
        assistantResponse = { content: span.outputs.choices[0].message.content };
      } else if (typeof span.outputs === "string") {
        assistantResponse = { content: span.outputs };
      } else if (span.outputs.output) {
        assistantResponse = { content: span.outputs.output };
      }
    }
  }

  return {
    userRequest,
    assistantResponse,
    toolSpans,
  };
}
