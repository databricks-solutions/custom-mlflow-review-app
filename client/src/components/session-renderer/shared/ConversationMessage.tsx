import React from "react";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface ConversationMessageProps {
  role: "user" | "assistant";
  content: string;
}

/**
 * Reusable component for displaying conversation messages
 * Used by both DefaultItemRenderer and ToolRenderer
 */
export function ConversationMessage({ role, content }: ConversationMessageProps) {
  const isUser = role === "user";
  
  return (
    <div className={`flex items-start gap-3 p-4 rounded-lg ${
      isUser ? "bg-blue-50" : "bg-green-50"
    }`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? "bg-blue-600" : "bg-green-600"
      }`}>
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>
      <div className="flex-1">
        <div className="font-medium text-sm mb-1">
          {isUser ? "User" : "Assistant"}
        </div>
        <div className="text-sm">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}