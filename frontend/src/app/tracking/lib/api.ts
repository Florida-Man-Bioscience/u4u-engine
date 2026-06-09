import type {
  BiomarkerCatalogEntry,
  CohortPeptideSummary,
  CohortResult,
  Measurement,
  Patient,
  Treatment,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://flmanbiosci.net/api/v1";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail: string | undefined;
    try {
      detail = (await res.json())?.detail;
    } catch {
      // ignore
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

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
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/tracking/measurements/csv`, {
    method: "POST",
    body: form,
  });
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
