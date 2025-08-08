export interface Assessment {
  name: string;
  value: any;
  rationale?: string;
  metadata?: Record<string, any>;
  source?: {
    source_type: string;
    source_id: string;
  };
}
