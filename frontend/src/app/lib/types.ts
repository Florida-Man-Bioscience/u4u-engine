export type Tier = "critical" | "high" | "medium" | "low";

export interface VariantResult {
  variant_id: string;
  rsid: string | null;
  location: string;
  consequence: string;
  genes: string[];
  clinvar: string | null;
  disease_name: string | null;
  gnomad_af: number | null;
  score: number;
  tier: Tier;
  reasons: string[];
  emoji: string;
  headline: string;
  consequence_plain: string;
  rarity_plain: string;
  clinvar_plain: string;
  action_hint: string;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "done" | "failed";
  progress_step?: string;
  progress_pct?: number;
  filename?: string;
  created_at?: string;
  error_message?: string;
  results?: VariantResult[];
  variant_count?: number;
}
