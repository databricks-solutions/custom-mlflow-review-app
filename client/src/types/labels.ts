export interface LabelValue {
  value: any;
  rationale?: string;
}

export type Labels = Record<string, LabelValue>;