// Mirrors the backend Pydantic models (claim_chart.models).

export interface Limitation {
  index: number;
  text: string;
}

export interface Mapping {
  limitation: string;
  disclosed: boolean;
  quote: string | null;
}

export interface ChartResult {
  limitations: Limitation[];
  mappings: Mapping[];
  verdict: string;
  novel_because: string[];
  disclaimer: string;
}

export interface Sample {
  name: string;
  claim: string;
  reference: string;
  note: string;
  tag: string;
}
