import type {
  BiomarkerDirection,
  BiomarkerModality,
  BiomarkerPurpose,
} from "@/app/lib/types";

export interface Patient {
  id: string;
  label: string;
  sex: string | null;
  birth_year: number | null;
  notes: string | null;
  created_at: string;
}

export interface Treatment {
  id: string;
  patient_id: string;
  peptide_name: string;
  dose: number | null;
  dose_unit: string | null;
  schedule: string | null;
  route: string | null;
  start_date: string;
  end_date: string | null;
  notes: string | null;
  created_at: string;
}

export interface Measurement {
  id: string;
  patient_id: string;
  treatment_id: string | null;
  biomarker_name: string;
  modality: string | null;
  value: number;
  unit: string | null;
  measured_at: string;
  notes: string | null;
  created_at: string;
}

export interface BiomarkerCatalogEntry {
  name: string;
  modality: BiomarkerModality;
  specimen: string;
  unit: string;
  direction: BiomarkerDirection;
  timeframe_weeks_min: number | null;
  timeframe_weeks_max: number | null;
  purpose: BiomarkerPurpose;
  effect_size: string | null;
  citation_apa: string | null;
  doi: string | null;
  doi_url: string | null;
  n_observed: number;
}

export interface CohortPeptideSummary {
  peptide_name: string;
  n_patients: number;
  n_treatments: number;
  n_measurements: number;
}

export interface TrajectoryPoint {
  patient_id: string;
  treatment_id: string;
  weeks_since_start: number;
  value: number;
  dose: number | null;
  dose_unit: string | null;
}

export interface TimeBin {
  weeks_label: number;
  n: number;
  median: number;
  q1: number;
  q3: number;
  min: number;
  max: number;
}

export interface DoseResponseRow {
  dose: number;
  dose_unit: string;
  n_patients: number;
  n_measurements: number;
  median_value: number;
  pct_change_from_baseline: number | null;
}

export interface CohortResult {
  peptide: string;
  biomarker_name: string;
  n_patients: number;
  n_measurements: number;
  expected: BiomarkerCatalogEntry | null;
  trajectories: TrajectoryPoint[];
  time_bins: TimeBin[];
  dose_response: DoseResponseRow[];
}

// ── Genetics + Bayesian predictions ────────────────────────────────────────

export interface GeneticVariant {
  rsid: string;
  gene: string;
  chromosome: string;
  genotype: "hom_ref" | "het" | "hom_alt";
  effect_allele: string;
  other_allele: string;
  dosage: number;
  peptide_effects: Record<string, number>;
  description: string;
}

export interface GeneticProfile {
  variants: GeneticVariant[];
  generated_at: string;
  source: string;
}

export interface GeneticsResponse {
  profile: GeneticProfile | null;
  source: string | null;
  created_at: string | null;
}

/**
 * Per-(peptide, biomarker) Normal prior on fractional change at the panel's
 * expected timeframe. Mean = r × expected_pct_panel; sd combines responder
 * uncertainty with panel-effect uncertainty.
 */
export interface GeneticPrior {
  peptide: string;
  biomarker: string;
  mean_pct_change: number;
  sd_pct_change: number;
  n_relevant_variants: number;
  aggregate_weight: number;
  expected_pct_panel: number;
  responder_mean: number;
  responder_sd: number;
}

/**
 * Per-peptide prior on the latent responder strength r. r = 1.0 means
 * "average responder"; r > 1.0 stronger; r < 1.0 weaker. Returned by
 * /tracking/patients/{id}/priors.
 */
export interface ResponderPrior {
  peptide: string;
  mean: number;
  sd: number;
  n_relevant_variants: number;
  aggregate_weight: number;
}

export interface Likelihood {
  mean_pct_change: number;
  sd_pct_change: number;
  n_observations: number;
  baseline: number;
}

export interface Posterior {
  mean_pct_change: number;
  sd_pct_change: number;
  credible_lo_95: number;
  credible_hi_95: number;
  n_effective: number;
}

export interface PredictivePoint {
  weeks_since_start: number;
  mean: number;
  lo_95: number;
  hi_95: number;
}

export interface PredictiveCurve {
  points: PredictivePoint[];
}

/**
 * Bayes-informed window in which the biomarker is expected to move.
 * weeks_min — first week the predicted effect reaches `detection_fraction`
 * of its asymptote; weeks_max — when it has effectively plateaued.
 * `credible` is True iff the 95% posterior CI on θ excludes 0.
 */
export interface ExpectedWindow {
  weeks_min: number;
  weeks_max: number;
  direction: "increase" | "decrease" | "inconclusive";
  asymptote_pct_change: number;
  credible: boolean;
  detection_fraction: number;
  plateau_fraction: number;
}

/**
 * Empirical-Bayes population prior derived from a leave-one-out cohort
 * of patients on the same (peptide, biomarker). When fewer than the
 * minimum number of donors contribute, or the cohort's spread is fully
 * explained by individual fit noise, this is null and the genetic prior
 * is used unchanged.
 */
export interface PopulationPrior {
  peptide: string;
  biomarker: string;
  n_donors: number;
  mean_pct_change: number;
  sd_pct_change: number;
  raw_total_sd: number;
  mean_within_sd: number;
}

export interface PredictionResult {
  patient_id: string;
  peptide: string;
  biomarker_name: string;
  expected: BiomarkerCatalogEntry | null;
  treatment_id: string | null;
  treatment_start: string | null;
  tau_weeks: number;
  baseline: number | null;
  n_measurements: number;
  /** Last week with an observed measurement. Past this point the chart
   *  is showing forward projection rather than fitted predictions. */
  last_observed_week: number | null;
  prior: GeneticPrior | null;
  population_prior: PopulationPrior | null;
  likelihood: Likelihood | null;
  posterior: Posterior;
  posterior_predictive: PredictiveCurve;
  prior_predictive: PredictiveCurve;
  expected_window: ExpectedWindow;
  prior_expected_window: ExpectedWindow;
}

// ── Model diagnostics (leave-one-out backtest) ─────────────────────────────

export interface DiagnosticsPoint {
  patient_id: string;
  patient_label: string;
  peptide: string;
  biomarker: string;
  weeks_since_start: number;
  baseline: number;
  predicted: number;
  predicted_lo_95: number;
  predicted_hi_95: number;
  observed: number;
  covered: boolean;
  /** Signed error as a percent of baseline (scale-free). */
  pct_error: number;
}

export interface DiagnosticsGroup {
  label: string;
  n_points: number;
  n_series: number;
  /** Fraction of held-out observations inside the 95% predictive band. */
  coverage_95: number | null;
  /** Mean absolute error as a percent of baseline. */
  mae_pct: number | null;
  rmse_pct: number | null;
  /** Mean signed error as a percent of baseline (systematic bias). */
  bias_pct: number | null;
}

export interface DiagnosticsResult {
  method: string;
  reference_path: string;
  min_series_points: number;
  n_patients: number;
  n_series: number;
  n_points: number;
  overall: DiagnosticsGroup;
  by_peptide: DiagnosticsGroup[];
  by_biomarker: DiagnosticsGroup[];
  points: DiagnosticsPoint[];
}
