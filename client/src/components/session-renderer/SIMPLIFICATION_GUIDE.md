# Renderer Simplification Guide

## 🎯 Goal
Make renderers simple, readable, and easy to fork by users who want to customize their MLflow trace evaluation UI.

## 📦 Shared Components Created

### 1. `ConversationMessage.tsx`
- Displays user/assistant messages with avatars
- Handles markdown rendering
- Consistent styling across renderers

### 2. `extractConversation.ts`
- Utility function to extract conversation from spans
- Handles deduplication
- Returns structured data

### 3. ~~`NavigationButtons.tsx`~~ 
- **UPDATE**: Navigation should be in parent `SMELabelingInterface.tsx`
- Renderers should ONLY render content, not handle navigation

## 🔧 Simplification Steps

### MAJOR CHANGE: Move ALL Navigation to Parent

**Current Problem**: Each renderer has 100+ lines of navigation code (Previous/Skip/Submit buttons)

**Solution**: Move ALL navigation to `SMELabelingInterface.tsx`:
```tsx
// In SMELabelingInterface.tsx, add after the RendererComponent:
<div className="flex items-center justify-between pt-6 border-t">
  <Button onClick={handleSkip} variant="outline">
    <XCircle className="h-4 w-4 mr-2" />
    Skip
  </Button>
  <Button 
    onClick={handleSubmitAndNext}
    disabled={assessments.size === 0}
  >
    <CheckCircle className="h-4 w-4 mr-2" />
    Submit & Next
  </Button>
</div>
```

**Benefits**:
- Removes 100+ lines from EACH renderer
- Navigation logic in ONE place
- Renderers focus ONLY on displaying content

### For ToolRenderer.tsx

1. **Use shared components:**
```tsx
import { ConversationMessage } from "./shared/ConversationMessage";
import { extractConversation } from "./shared/extractConversation";

// Replace lines 342-444 with:
const { userRequest, assistantResponse, toolSpans } = extractConversation(traceData?.spans || []);

// Replace lines 468-481 with:
{userRequest && <ConversationMessage role="user" content={userRequest.content} />}

// Replace lines 561-575 with:
{assistantResponse && <ConversationMessage role="assistant" content={assistantResponse.content} />}
```

2. **Simplify assessment handling:**
```tsx
// Remove complex update logic (lines 164-179, 200-217)
// Just create new assessments:
const handleAssessmentSave = async (assessment: Assessment) => {
  const traceId = item?.source?.trace_id;
  if (!traceId || !assessment.value) return;
  
  const schema = reviewApp?.labeling_schemas?.find(s => s.name === assessment.name);
  const isExpectation = schema?.type === 'EXPECTATION';
  
  try {
    if (isExpectation) {
      await logExpectationMutation.mutateAsync({
        traceId,
        expectationKey: assessment.name,
        expectationValue: assessment.value,
        rationale: assessment.rationale
      });
    } else {
      await logFeedbackMutation.mutateAsync({
        traceId,
        feedbackKey: assessment.name,
        feedbackValue: assessment.value,
        rationale: assessment.rationale
      });
    }
    toast.success(`Saved ${assessment.name}`);
  } catch (error) {
    toast.error(`Failed to save ${assessment.name}`);
  }
};
```

### For DefaultItemRenderer.tsx

1. **Use shared components:**
```tsx
import { ConversationMessage } from "./shared/ConversationMessage";
import { extractConversation } from "./shared/extractConversation";

// Replace lines 330-432 with:
const { userRequest, assistantResponse } = extractConversation(traceData?.spans || []);

// Replace lines 445-459 with:
{userRequest && <ConversationMessage role="user" content={userRequest.content} />}

// Replace lines 463-477 with:
{assistantResponse && <ConversationMessage role="assistant" content={assistantResponse.content} />}

// DELETE lines 673-808 (entire navigation section)
// Navigation is now handled by parent component
```

2. **Extract accordion to component:**
```tsx
// Create AssessmentAccordion.tsx component for lines 488-572 and 582-666
// This removes ~180 lines of duplication
```

## 📚 Best Practices for Forking

### 1. Start Simple
- Copy one of the simplified renderers
- Modify only what you need
- Use shared components where possible

### 2. Focus on Your Use Case
- Remove features you don't need
- Add domain-specific UI elements
- Keep business logic minimal

### 3. Example Custom Renderer
```tsx
import { ConversationMessage } from "./shared/ConversationMessage";
import { NavigationButtons } from "./shared/NavigationButtons";
import { extractConversation } from "./shared/extractConversation";

export function MyCustomRenderer(props: ItemRendererProps) {
  const { userRequest, assistantResponse } = extractConversation(props.traceData?.spans || []);
  
  return (
    <div className="space-y-4">
      {/* Your custom UI here */}
      {userRequest && <ConversationMessage role="user" content={userRequest.content} />}
      {assistantResponse && <ConversationMessage role="assistant" content={assistantResponse.content} />}
      
      {/* Your custom assessment form */}
      <YourCustomAssessmentForm />
      
      {/* Reuse navigation */}
      <NavigationButtons {...navigationProps} />
    </div>
  );
}
```

## 🎨 Styling Customization

### Colors
- User messages: `bg-blue-50` with `bg-blue-600` avatar
- Assistant messages: `bg-green-50` with `bg-green-600` avatar
- Tool calls: `bg-muted/20` with `border`

### Layout
- Two-column grid on large screens
- Conversation on left, assessments on right
- Navigation buttons full width at bottom

## 📉 Complexity Reduction

### Before
- ToolRenderer: 657 lines
- DefaultItemRenderer: 811 lines
- Total: 1,468 lines

### After (with navigation moved to parent)
- ToolRenderer: ~300 lines (removed 357 lines!)
- DefaultItemRenderer: ~250 lines (removed 561 lines!)
- Shared components: ~150 lines
- SMELabelingInterface: +50 lines (navigation logic)
- Total: ~750 lines
- **Reduction: 49%**

### Benefits
1. **Less duplication** - Shared logic in one place
2. **Easier to understand** - Clear separation of concerns
3. **Faster customization** - Start with working components
4. **Consistent UX** - Same patterns across renderers