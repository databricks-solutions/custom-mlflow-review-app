// Types for custom renderer system

export interface TraceData {
  info: {
    trace_id: string;
    request_time: string;
    execution_duration?: string;
    state?: string;
  };
  spans: Array<{
    name: string;
    type: string;
    inputs?: any;
    outputs?: any;
  }>;
}

export interface LabelingItem {
  item_id: string;
  state: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED";
  labels?: Record<string, any>;
  comment?: string;
  source?: {
    trace_id: string;
  };
}

export interface LabelingSchema {
  name: string;
  title?: string;
  instruction?: string;
  type: "FEEDBACK" | "EXPECTATION";
  numeric?: {
    min_value: number;
    max_value: number;
  };
  categorical?: {
    options: string[];
  };
  text?: {
    max_length?: number;
  };
  enable_comment?: boolean;
}

export interface ReviewApp {
  review_app_id: string;
  experiment_id: string;
  labeling_schemas: LabelingSchema[];
}

export interface LabelingSession {
  labeling_session_id: string;
  name: string;
  mlflow_run_id: string;
  assigned_users: string[];
  labeling_schemas: LabelingSchema[];
}

export interface ItemRendererProps {
  // Core data
  item: LabelingItem;
  traceData: TraceData;
  reviewApp: ReviewApp;
  session: LabelingSession;
  
  // Navigation
  currentIndex: number;
  totalItems: number;
  
  // State management
  labels: Record<string, any>;
  onLabelsChange: (labels: Record<string, any>) => void;
  
  // Actions - updated to include auto-save capability
  onUpdateItem: (itemId: string, updates: { state?: string; labels?: Record<string, any>; comment?: string }) => Promise<any>;
  onNavigateToIndex: (index: number) => void;
  
  // UI state
  isLoading?: boolean;
  isSubmitting?: boolean;
}

export interface ItemRenderer {
  name: string;
  displayName: string;
  description: string;
  component: React.ComponentType<ItemRendererProps>;
}

export interface RendererRegistry {
  renderers: Map<string, ItemRenderer>;
  defaultRenderer: string;
  getRenderer: (name?: string) => ItemRenderer;
  registerRenderer: (renderer: ItemRenderer) => void;
  listRenderers: () => ItemRenderer[];
}