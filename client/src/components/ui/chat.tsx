import * as React from "react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// ChatBubble
interface ChatBubbleProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "sent" | "received";
}

const ChatBubble = React.forwardRef<HTMLDivElement, ChatBubbleProps>(
  ({ className, variant = "received", children, ...props }, ref) => {
    return (
      <div
        className={cn(
          "flex gap-2 max-w-[70%]",
          variant === "sent" ? "flex-row-reverse self-end" : "self-start",
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }
);
ChatBubble.displayName = "ChatBubble";

// ChatBubbleAvatar
interface ChatBubbleAvatarProps {
  src?: string;
  fallback?: string;
  className?: string;
}

const ChatBubbleAvatar: React.FC<ChatBubbleAvatarProps> = ({ src, fallback = "AI", className }) => {
  return (
    <Avatar className={cn("h-8 w-8", className)}>
      <AvatarImage src={src} alt="Avatar" />
      <AvatarFallback>{fallback}</AvatarFallback>
    </Avatar>
  );
};

// ChatBubbleMessage
interface ChatBubbleMessageProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "sent" | "received";
  isLoading?: boolean;
}

const ChatBubbleMessage = React.forwardRef<HTMLDivElement, ChatBubbleMessageProps>(
  ({ className, variant = "received", isLoading = false, children, ...props }, ref) => {
    return (
      <div
        className={cn(
          "rounded-lg px-3 py-2 text-sm",
          variant === "sent" ? "bg-primary text-primary-foreground" : "bg-muted",
          isLoading && "animate-pulse",
          className
        )}
        ref={ref}
        {...props}
      >
        {isLoading ? (
          <div className="flex space-x-1">
            <div className="h-2 w-2 bg-current rounded-full animate-bounce" />
            <div className="h-2 w-2 bg-current rounded-full animate-bounce delay-75" />
            <div className="h-2 w-2 bg-current rounded-full animate-bounce delay-150" />
          </div>
        ) : (
          children
        )}
      </div>
    );
  }
);
ChatBubbleMessage.displayName = "ChatBubbleMessage";

// ChatBubbleTimestamp
interface ChatBubbleTimestampProps extends React.HTMLAttributes<HTMLDivElement> {
  timestamp: string;
}

const ChatBubbleTimestamp: React.FC<ChatBubbleTimestampProps> = ({
  timestamp,
  className,
  ...props
}) => {
  return (
    <div className={cn("text-xs text-muted-foreground mt-1", className)} {...props}>
      {timestamp}
    </div>
  );
};

// ChatMessageList
interface ChatMessageListProps extends React.HTMLAttributes<HTMLDivElement> {}

const ChatMessageList = React.forwardRef<HTMLDivElement, ChatMessageListProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className={cn("flex flex-col gap-4 p-4", className)} ref={ref} {...props}>
        {children}
      </div>
    );
  }
);
ChatMessageList.displayName = "ChatMessageList";

// ChatInput
interface ChatInputProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const ChatInput = React.forwardRef<HTMLTextAreaElement, ChatInputProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
ChatInput.displayName = "ChatInput";

export {
  ChatBubble,
  ChatBubbleAvatar,
  ChatBubbleMessage,
  ChatBubbleTimestamp,
  ChatMessageList,
  ChatInput,
};
