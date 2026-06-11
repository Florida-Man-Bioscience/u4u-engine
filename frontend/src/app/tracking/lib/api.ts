import type {
  BiomarkerCatalogEntry,
  CohortPeptideSummary,
  CohortResult,
  GeneticsResponse,
  Measurement,
  Patient,
  PredictionResult,
  ResponderPrior,
  Treatment,
} from "./types";
import { API_BASE, authFetch, getToken } from "../../lib/authFetch";

// All tracking calls share the centralised authFetch wrapper so the
// bearer token + 401 redirect behaviour is identical across modules.
const req = authFetch;

// ── Patients ──────────────────────────────────────────────────────────────

export const listPatients = () => req<Patient[]>("/tracking/patients");

export const getPatient = (id: string) => req<Patient>(`/tracking/patients/${id}`);

export const createPatient = (body: {
  label: string;
  sex?: string | null;
  birth_year?: number | null;
  notes?: string | null;
}) =>
  req<Patient>("/tracking/patients", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const deletePatient = (id: string) =>
  req<{ deleted: boolean }>(`/tracking/patients/${id}`, { method: "DELETE" });

// ── Treatments ─────────────────────────────────────────────────────────────

export const listTreatments = (patientId: string) =>
  req<Treatment[]>(`/tracking/patients/${patientId}/treatments`);

export const createTreatment = (
  patientId: string,
  body: Omit<Treatment, "id" | "patient_id" | "created_at">
) =>
  req<Treatment>(`/tracking/patients/${patientId}/treatments`, {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Measurements ───────────────────────────────────────────────────────────

export const listMeasurements = (patientId: string, biomarker?: string) => {
  const qs = biomarker ? `?biomarker=${encodeURIComponent(biomarker)}` : "";
  return req<Measurement[]>(`/tracking/patients/${patientId}/measurements${qs}`);
};

export const createMeasurement = (body: {
  patient_id: string;
  biomarker_name: string;
  value: number;
  measured_at: string;
  treatment_id?: string | null;
  modality?: string | null;
  unit?: string | null;
  notes?: string | null;
}) =>
  req<Measurement>("/tracking/measurements", {
    method: "POST",
    body: JSON.stringify(body),
  });

export async function uploadMeasurementCsv(file: File) {
  // Multipart upload — bypass authFetch's default JSON headers but still
  // attach the bearer token manually.
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/tracking/measurements/csv`, {
    method: "POST",
    body: form,
    headers,
  });
  if (res.status === 401) {
    // Mirror authFetch's redirect semantics.
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Session expired — please sign in again.");
  }
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = (await res.json())?.detail;
    } catch {
      // ignore
    }
    throw new Error(
      typeof detail === "string" ? detail : `CSV upload failed (HTTP ${res.status})`
    );
  }
  return res.json() as Promise<{ created: number; errors: string[] }>;
}

// ── Catalog + cohort ───────────────────────────────────────────────────────

export const listPeptidesWithData = () =>
  req<CohortPeptideSummary[]>("/tracking/peptides");

export const getBiomarkerCatalog = (peptide: string) =>
  req<BiomarkerCatalogEntry[]>(
    `/tracking/peptides/${encodeURIComponent(peptide)}/biomarkers`
  );

export const getGenetics = (patientId: string) =>
  req<GeneticsResponse>(`/tracking/patients/${patientId}/genetics`);

export const regenerateGenetics = (patientId: string, seed?: number) => {
  const qs = seed !== undefined ? `?seed=${seed}` : "";
  return req<GeneticsResponse>(
    `/tracking/patients/${patientId}/genetics/synthetic${qs}`,
    { method: "POST", body: "{}" },
  );
};

export const getPriors = (patientId: string) =>
  req<{ priors: ResponderPrior[] }>(`/tracking/patients/${patientId}/priors`);

export const getPrediction = (
  patientId: string,
  peptide: string,
  biomarker: string,
) => {
  const u = new URLSearchParams({ peptide, biomarker });
  return req<PredictionResult>(
    `/tracking/patients/${patientId}/predictions?${u.toString()}`,
  );
};

export interface SeedResult {
  patients: number;
  treatments: number;
  measurements: number;
  skipped: number;
}

export const seedDemoData = (body: {
  force?: boolean;
  patients?: number;
  seed?: number;
}) =>
  req<SeedResult>("/tracking/seed", {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });

export const getCohort = (params: {
  peptide: string;
  biomarker: string;
  dose_min?: number;
  dose_max?: number;
}) => {
  const u = new URLSearchParams();
  u.set("peptide", params.peptide);
  u.set("biomarker", params.biomarker);
  if (params.dose_min !== undefined) u.set("dose_min", String(params.dose_min));
  if (params.dose_max !== undefined) u.set("dose_max", String(params.dose_max));
  return req<CohortResult>(`/tracking/cohort?${u.toString()}`);
};
