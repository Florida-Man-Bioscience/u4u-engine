import type {
  BiomarkerDirection,
  BiomarkerModality,
  BiomarkerPurpose,
} from "../../lib/types";

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
