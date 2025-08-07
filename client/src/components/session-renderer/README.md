# Session Renderer System

This directory contains the complete session renderer system for MLflow trace review. Users can create custom React components to control how traces and labeling schemas are displayed in the UI.

## ✨ System Overview

The session renderer system allows users to:
- **Customize trace display** - Show conversation flows, timelines, or any custom layout
- **Control labeling schema placement** - Determine where and how assessments appear
- **Work with Claude Code** - Get AI assistance to create and modify renderers
- **Switch renderers dynamically** - Change the UI for different labeling sessions

## 🚀 Quick Start

### 1. Choose a Renderer (Dev Mode)

In development mode, use the **Renderer Selector** to choose how traces are displayed:

1. Navigate to any labeling session in dev mode (`?mode=dev`)
2. Use the **Custom Renderer** card to select from available options
3. Apply the renderer - it will be saved to the MLflow run tags
4. Switch to SME mode to see the new renderer in action

### 2. Available Renderers

- **Default Renderer** - Standard conversation view with full labeling forms
- **Compact Timeline** - Timeline-based view with quick stats and streamlined interface

## 🛠️ Creating Custom Renderers

### Step 1: Create Your Renderer Component

```tsx
// components/session-renderer/renderers/MyAnalysisRenderer.tsx
import { ItemRendererProps } from "@/types/renderers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function MyAnalysisRenderer({
  item,
  traceData,
  reviewApp,
  labels,
  onLabelsChange,
  onSubmit,
  currentIndex,
  totalItems,
}: ItemRendererProps) {
  // Extract spans for analysis
  const spans = traceData?.spans || [];
  const chatSpans = spans.filter(s => s.type === "CHAT_MODEL");
  const toolSpans = spans.filter(s => s.type === "TOOL");

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Conversation Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4>Chat Interactions: {chatSpans.length}</h4>
              {/* Your custom chat analysis */}
            </div>
            <div>
              <h4>Tool Usage: {toolSpans.length}</h4>
              {/* Your custom tool analysis */}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Custom labeling interface */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          {reviewApp?.labeling_schemas?.map((schema) => (
            <div key={schema.name}>
              {/* Your custom schema rendering */}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Button onClick={() => onSubmit("SKIPPED")} variant="outline">
          Skip
        </Button>
        <Button onClick={() => onSubmit("COMPLETED")}>
          Submit
        </Button>
      </div>
    </div>
  );
}
```

### Step 2: Register Your Renderer

```tsx
// components/session-renderer/renderers/index.ts - Add to the constructor:
this.registerRenderer({
  name: "analysis-focused",
  displayName: "Analysis Focused",
  description: "Specialized renderer for detailed conversation and tool analysis",
  component: MyAnalysisRenderer,
});
```

### Step 3: Use Your Renderer

1. **In Dev Mode**: Select your renderer from the dropdown
2. **Via Claude**: Ask Claude to create and register new renderers
3. **Programmatically**: Set the `mlflow.customRenderer` tag on MLflow runs

## 🎯 Available Props

Your renderer component receives comprehensive props:

### Core Data
- `item: LabelingItem` - Current labeling item with state and labels
- `traceData: TraceData` - Complete trace information with spans
- `reviewApp: ReviewApp` - Review app with labeling schemas
- `session: LabelingSession` - Current labeling session details

### Navigation & State
- `currentIndex: number` - Current item position (0-based)
- `totalItems: number` - Total items in session
- `labels: Record<string, any>` - Current label values
- `comment: string` - Current comment text

### Event Handlers
- `onLabelsChange: (labels) => void` - Update label values
- `onCommentChange: (comment) => void` - Update comment
- `onSubmit: (state) => void` - Submit with "COMPLETED" or "SKIPPED"
- `onPrevious: () => void` - Navigate to previous item
- `onNext: () => void` - Navigate to next item
- `onNavigateToIndex: (index) => void` - Jump to specific item

### UI State
- `isLoading?: boolean` - Whether trace data is loading
- `isSubmitting?: boolean` - Whether submission is in progress

## 📊 Data Structures

### TraceData Structure
```typescript
{
  info: {
    trace_id: string;
    request_time: string;
    execution_duration?: string;
    state?: string;
  },
  spans: Array<{
    name: string;
    type: "CHAT_MODEL" | "TOOL" | string;
    inputs?: any;    // Chat messages, tool parameters
    outputs?: any;   // AI responses, tool results
  }>
}
```

### LabelingSchema Types
```typescript
{
  name: string;
  title?: string;
  instruction?: string;
  numeric?: { min_value: number; max_value: number; };
  categorical?: { options: string[]; };
  text?: { max_length?: number; };
  enable_comment?: boolean;
}
```

## 🔧 Working with Claude Code

Claude can help you create custom renderers with natural language:

### Example Prompts:

**"Create a renderer focused on tool usage analysis"**
```
Claude will:
1. Create a new renderer component
2. Focus on TOOL spans and their input/output
3. Add custom analysis and visualizations
4. Register it in the system
```

**"Add a compact card-based renderer for mobile review"**
```
Claude will:
1. Design a mobile-friendly layout
2. Use cards for compact information display
3. Optimize labeling forms for touch interaction
4. Ensure responsive design
```

**"Build a renderer that highlights errors and performance issues"**
```
Claude will:
1. Analyze trace data for error indicators
2. Highlight slow operations and failures
3. Create specialized error-focused labeling schemas
4. Add performance metrics display
```

## 🎨 Design Guidelines

### UI Consistency
- Use shadcn/ui components for consistent styling
- Follow the existing color scheme and spacing
- Maintain accessibility standards

### Performance
- Efficiently process span data
- Use React optimization patterns (useMemo, useCallback)
- Handle large traces gracefully

### User Experience
- Provide clear navigation between items
- Show progress indicators
- Give immediate feedback for user actions
- Handle loading and error states

## 🔧 Technical Architecture

### Registry System
- **RendererRegistry**: Manages all available renderers
- **Dynamic Loading**: Renderers are resolved at runtime
- **Type Safety**: Full TypeScript support throughout

### MLflow Integration
- **Tag-Based Selection**: Uses `mlflow.customRenderer` run tag
- **Automatic Persistence**: Renderer choice is saved to MLflow
- **Fallback Handling**: Graceful fallback to default renderer

### State Management
- **React Query**: Handles data fetching and caching
- **Local State**: Manages form state and navigation
- **Optimistic Updates**: Immediate UI feedback

## 📝 Examples in Action

### Timeline Renderer Features:
- **Compact Event Display** - Shows chat and tool events in chronological order
- **Quick Stats** - Displays conversation metrics at a glance
- **Streamlined Forms** - Optimized labeling interface for speed
- **Visual Indicators** - Color-coded event types and status

### Default Renderer Features:
- **Full Conversation View** - Complete chat bubble interface
- **Detailed Tool Display** - Expanded input/output information
- **Comprehensive Forms** - Full labeling schema presentation
- **Progress Tracking** - Visual progress indicators

## 🚀 Future Extensibility

The system is designed for easy extension:

- **Plugin Architecture** - Add new renderer types easily
- **Component Library** - Reusable UI components for consistency
- **Theme Support** - Ready for custom themes and branding
- **Export Capabilities** - Framework for adding export features

## 💡 Best Practices

1. **Start Simple** - Begin with the default renderer and customize incrementally
2. **Test Thoroughly** - Verify your renderer works with different trace types
3. **Document Usage** - Add clear descriptions for your custom renderers
4. **Handle Edge Cases** - Account for missing data and error states
5. **Ask Claude** - Use AI assistance for complex customizations

The custom renderer system puts complete control over the trace review experience in your hands, with the full power of Claude Code to help you build exactly what you need.