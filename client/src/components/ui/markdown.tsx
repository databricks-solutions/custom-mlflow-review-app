import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { cn } from "@/lib/utils";

interface MarkdownProps {
  content: string;
  className?: string;
  variant?: "default" | "compact" | "large";
}

export const Markdown: React.FC<MarkdownProps> = ({ content, className, variant = "default" }) => {
  const variantClasses = {
    default: "prose prose-slate prose-base max-w-none",
    compact: "prose prose-slate prose-sm max-w-none",
    large: "prose prose-slate prose-lg max-w-none",
  };

  return (
    <div
      className={cn(
        variantClasses[variant],
        "dark:prose-invert markdown-content",
        "prose-headings:scroll-m-20 prose-headings:tracking-tight",
        "prose-h1:font-bold prose-h1:text-3xl prose-h1:lg:text-4xl prose-h1:border-b prose-h1:pb-2 prose-h1:mb-4",
        "prose-h2:font-semibold prose-h2:text-2xl prose-h2:lg:text-3xl prose-h2:mt-8 prose-h2:mb-4",
        "prose-h3:font-semibold prose-h3:text-xl prose-h3:lg:text-2xl prose-h3:mt-6 prose-h3:mb-3",
        "prose-h4:font-semibold prose-h4:text-lg prose-h4:mt-4 prose-h4:mb-2",
        "prose-p:leading-7 prose-p:[&:not(:first-child)]:mt-6",
        "prose-a:font-medium prose-a:text-primary prose-a:underline prose-a:underline-offset-4",
        "prose-a:hover:text-primary/80",
        "prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-6 prose-blockquote:mt-6",
        "prose-blockquote:italic prose-blockquote:text-muted-foreground prose-blockquote:bg-muted/50 prose-blockquote:rounded-r-md prose-blockquote:py-3",
        "prose-code:relative prose-code:rounded prose-code:bg-muted prose-code:px-[0.3rem] prose-code:py-[0.2rem]",
        "prose-code:text-sm prose-code:font-mono prose-code:font-medium",
        "prose-pre:overflow-x-auto prose-pre:rounded-lg prose-pre:border prose-pre:bg-card prose-pre:p-4 prose-pre:shadow-sm prose-pre:my-6",
        "prose-ul:my-6 prose-ul:ml-6 prose-ul:list-disc prose-ul:[&>li]:mt-2",
        "prose-ol:my-6 prose-ol:ml-6 prose-ol:list-decimal prose-ol:[&>li]:mt-2",
        "prose-li:marker:text-muted-foreground prose-li:leading-7",
        "prose-table:w-full prose-table:border-collapse prose-table:overflow-hidden prose-table:rounded-md prose-table:border prose-table:my-6 prose-table:shadow-sm",
        "prose-th:border prose-th:border-border prose-th:bg-muted prose-th:p-3 prose-th:text-left prose-th:font-semibold",
        "prose-td:border prose-td:border-border prose-td:p-3",
        "prose-tbody:prose-tr:hover:bg-muted/50",
        "prose-strong:font-semibold prose-strong:text-foreground",
        "prose-em:italic",
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom heading components with better styling
          h1: ({ children, ...props }) => (
            <h1
              className="scroll-m-20 text-3xl font-bold tracking-tight lg:text-4xl border-b border-border pb-2 mb-4 text-foreground"
              {...props}
            >
              {children}
            </h1>
          ),
          h2: ({ children, ...props }) => (
            <h2
              className="scroll-m-20 text-2xl font-semibold tracking-tight lg:text-3xl mt-8 mb-4 text-foreground"
              {...props}
            >
              {children}
            </h2>
          ),
          h3: ({ children, ...props }) => (
            <h3
              className="scroll-m-20 text-xl font-semibold tracking-tight lg:text-2xl mt-6 mb-3 text-foreground"
              {...props}
            >
              {children}
            </h3>
          ),
          h4: ({ children, ...props }) => (
            <h4
              className="scroll-m-20 text-lg font-semibold tracking-tight mt-4 mb-2 text-foreground"
              {...props}
            >
              {children}
            </h4>
          ),
          // Enhanced code blocks
          pre: ({ children, ...props }) => (
            <pre
              className="overflow-x-auto rounded-lg border bg-card p-4 text-sm shadow-sm my-6 text-foreground"
              {...props}
            >
              {children}
            </pre>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code
                  className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-medium text-foreground"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={cn("font-mono text-sm", className)} {...props}>
                {children}
              </code>
            );
          },
          // Better blockquotes
          blockquote: ({ children, ...props }) => (
            <blockquote
              className="mt-6 border-l-4 border-primary pl-6 py-3 bg-muted/50 rounded-r-md italic text-muted-foreground"
              {...props}
            >
              {children}
            </blockquote>
          ),
          // Enhanced tables
          table: ({ children, ...props }) => (
            <div className="my-6 w-full overflow-y-auto">
              <table
                className="w-full border-collapse overflow-hidden rounded-md border shadow-sm"
                {...props}
              >
                {children}
              </table>
            </div>
          ),
          thead: ({ children, ...props }) => (
            <thead className="bg-muted" {...props}>
              {children}
            </thead>
          ),
          th: ({ children, ...props }) => (
            <th
              className="border border-border bg-muted p-3 text-left font-semibold text-foreground"
              {...props}
            >
              {children}
            </th>
          ),
          td: ({ children, ...props }) => (
            <td className="border border-border p-3 text-foreground" {...props}>
              {children}
            </td>
          ),
          tbody: ({ children, ...props }) => (
            <tbody className="[&>tr:hover]:bg-muted/50" {...props}>
              {children}
            </tbody>
          ),
          // Better lists
          ul: ({ children, ...props }) => (
            <ul className="my-6 ml-6 list-disc [&>li]:mt-2 [&>li]:leading-7" {...props}>
              {children}
            </ul>
          ),
          ol: ({ children, ...props }) => (
            <ol className="my-6 ml-6 list-decimal [&>li]:mt-2 [&>li]:leading-7" {...props}>
              {children}
            </ol>
          ),
          // Enhanced links
          a: ({ children, href, ...props }) => (
            <a
              href={href}
              className="font-medium text-primary underline underline-offset-4 hover:text-primary/80 transition-colors"
              target={href?.startsWith("http") ? "_blank" : undefined}
              rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
              {...props}
            >
              {children}
            </a>
          ),
          // Better paragraphs
          p: ({ children, ...props }) => (
            <p className="leading-7 [&:not(:first-child)]:mt-6 text-foreground" {...props}>
              {children}
            </p>
          ),
          // Enhanced strong/bold
          strong: ({ children, ...props }) => (
            <strong className="font-semibold text-foreground" {...props}>
              {children}
            </strong>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
