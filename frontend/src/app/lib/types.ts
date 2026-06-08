export type Tier = "critical" | "high" | "medium" | "low";

export interface JobListItem {
  job_id: string;
  status: "pending" | "running" | "done" | "failed";
  filename: string;
  file_size: number;
  count: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  progress: { step: string; pct: number };
  error: string | null;
}

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

export interface Bpc157PathwayHit {
  pathway: string;
  display_name: string;
  genes_hit: string[];
  total_genes: number;
  coverage: number;
  relevance: string;
}

export interface Bpc157CandidateFactor {
  rsid: string;
  gene: string;
  pathway: string;
  direction: string;
  effect: string;
}

export interface Bpc157Biomarker {
  name: string;
  expected_change: string;
  category: string;
}

export interface Bpc157Prediction {
  responder_tier: "likely_good" | "possible" | "uncertain" | "low_confidence";
  composite_score: number;
  pathways_affected: Bpc157PathwayHit[];
  primary_use_case: string;
  primary_use_case_display: string;
  primary_use_case_description: string;
  biomarker_recommendations: Bpc157Biomarker[];
  candidate_factors: Bpc157CandidateFactor[];
  summary_text: string;
  disclaimer: string;
}

export interface BiomarkerPanel {
  peptide: string;
  off_label_uses: string[];
  efficacy_markers: string[];
  safety_markers: string[];
  citation_apa: string;
  doi: string;
  doi_url: string | null;
}

export interface PeptideRecommendation {
  peptide_name: string;
  genes_for_genotyping: string[];
  genes_found: string[];
  genes_missing: string[];
  coverage: number;
  predicted_tier: string;
  prediction_description: string;
  tier_reasons: string[];
  rationale: string;
  references: string[];
  category: string;
  category_display: string;
  relevant_variants: VariantResult[];
  bpc157_prediction?: Bpc157Prediction;
  biomarker_panel?: BiomarkerPanel | null;
}

export interface PeptideMapping {
  recommendations: PeptideRecommendation[];
  summary_text: string;
  genes_found_total: string[];
  peptides_with_coverage: number;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "done" | "failed";
  progress_step?: string;
  progress_pct?: number;
  filename?: string;
  created_at?: string;
  error_message?: string;
  results?: {
    variants?: VariantResult[];
    peptide_recommendations?: PeptideMapping;
    pathway_summary?: unknown;
    receptor_genetics?: unknown;
    prs_profile?: unknown;
    ar_cag_repeat?: unknown;
    pgx_profile?: PGxProfile;
  };
  partial_results?: VariantResult[];
  variant_count?: number;
}

/* ── Pharmacogenomics ────────────────────────────────────────────────────── */

export type PGxPhenotype = "PM" | "IM" | "NM" | "RM" | "UM" | "IND";

export interface StarAlleleCall {
  gene: string;
  diplotype: string;
  activity_score: number | null;
  phenotype: PGxPhenotype;
  callers_agreed: string[];
  confidence: number;
  evidence_tier: string;
  raw_calls: Record<string, string>;
}

export interface HLACall {
  locus: string;
  present: boolean;
  method: string;
  tag_rsid: string | null;
  risk_drugs: string[];
}

export interface DrugRecommendation {
  drug: string;
  gene: string;
  phenotype: PGxPhenotype;
  recommendation: string;
  classification: "strong" | "moderate" | "optional";
  cpic_guideline_id: string | null;
  source: string;
}

export interface DrugPrediction {
  drug: string;
  point_score: number;
  prediction_set: string[]; // {"respond","non_respond","indeterminate"}
  confidence_level: number;
  contributing_genes: string[];
  method: string;
}

export interface PRSResult {
  trait: string;
  score: number;
  percentile: number | null;
  risk_tier: "low" | "intermediate" | "high";
  n_variants_used: number;
  n_variants_expected: number;
  drug_context: string[];
}

export interface PGxProfile {
  star_alleles: StarAlleleCall[];
  hla_calls: HLACall[];
  recommendations: DrugRecommendation[];
  prs_results: PRSResult[];
  drug_predictions: DrugPrediction[];
  phenoconversion_notes: string[];
  input_path: string;
  summary_text: string;
}

export interface DrugDetail {
  drug: string;
  recommendations: DrugRecommendation[];
  prs: PRSResult[];
  prediction: DrugPrediction | null;
  hla_warnings: HLACall[];
}

/* ── Regulatory dashboard ─────────────────────────────────────────────────── */

export type RegulatoryCategorySlug =
  | "cat1"
  | "cat2"
  | "removed_from_cat2"
  | "pcac_review"
  | "unscheduled";

export interface RegulatoryCategory {
  label: string;
  color: "green" | "red" | "purple" | "amber" | "gray";
  description: string;
}

export interface RegulatoryHistoryEntry {
  date: string;
  status: RegulatoryCategorySlug;
  note: string;
}

export type LiveSourceStatus = "fresh" | "stale" | "unavailable";

export interface LiveEnvelope<T> {
  data: T | null;
  fetched_at: number | null;
  status: LiveSourceStatus;
  source: string;
}

export interface ClinicalTrialsLive {
  search_term: string;
  total_trials: number;
  active_trials: number;
  latest_phase: string | null;
  recent_studies: Array<{
    nct_id: string;
    title: string | null;
    status: string | null;
    phase: string | null;
    url: string;
  }>;
}

export interface OpenFdaLive {
  search_term: string;
  recalls_total: number;
  recalls: Array<{
    recall_number: string | null;
    reason: string | null;
    status: string | null;
    classification: string | null;
    report_date: string | null;
    product_description: string | null;
  }>;
  adverse_events_total: number | null;
}

export interface FederalRegisterLive {
  search_term: string;
  total: number;
  documents: Array<{
    title: string | null;
    document_number: string | null;
    publication_date: string | null;
    url: string | null;
    abstract: string | null;
  }>;
}

export interface PeptideLiveData {
  clinicaltrials?: LiveEnvelope<ClinicalTrialsLive>;
  openfda?: LiveEnvelope<OpenFdaLive>;
  federal_register?: LiveEnvelope<FederalRegisterLive>;
}

export interface RegulatoryPeptide {
  slug: string;
  name: string;
  aliases: string[];
  category: RegulatoryCategorySlug;
  pcac_wave: "july_2026" | "early_2027" | null;
  medspa_uses: string[];
  history: RegulatoryHistoryEntry[];
  clinicaltrials_search_term: string;
  openfda_search_term: string;
  federal_register_search_term: string;
  engine_covered: boolean;
  live: PeptideLiveData;
}

export interface RegulatoryPeptidesPayload {
  categories: Record<RegulatoryCategorySlug, RegulatoryCategory>;
  peptides: RegulatoryPeptide[];
  stats: {
    by_category: Partial<Record<RegulatoryCategorySlug, number>>;
    by_pcac_wave: Partial<Record<"july_2026" | "early_2027", number>>;
    total_peptides: number;
  };
  last_curated: string | null;
}

export interface RegulatoryEvent {
  date: string;
  title: string;
  kind: "category_change" | "policy" | "pcac" | "deadline" | "rulemaking";
  status: "past" | "upcoming" | "tbd";
  impact: string;
  source_url: string;
  source_label: string;
}

export interface RegulatorySource {
  label: string;
  url: string;
  description: string;
}

export interface DocketLiveSummary {
  docket_id: string;
  comments_count: number | null;
  last_comment_posted_at: string | null;
  docket_url: string;
}

export interface RegulatoryEventsPayload {
  events: RegulatoryEvent[];
  official_sources: RegulatorySource[];
  pcac_contact: {
    name: string;
    email: string;
    role: string;
  } | null;
  regulations_gov_docket_id: string | null;
  docket_live: LiveEnvelope<DocketLiveSummary> | null;
  last_curated: string | null;
}
