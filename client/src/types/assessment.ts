import { JsonValue } from "./renderers";

export interface Assessment {
  assessment_id?: string;
  name: string;
  value: JsonValue;
  type?: 'feedback' | 'expectation';
  rationale?: string;
  metadata?: Record<string, JsonValue>;
  source?: {
    source_type: string;
    source_id: string;
  } | string;
  timestamp?: string;
}
