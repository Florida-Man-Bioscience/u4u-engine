import type {
  JobStatus,
  JobListItem,
  PGxProfile,
  DrugDetail,
  RegulatoryPeptidesPayload,
  RegulatoryEventsPayload,
} from "./types";
import { authFetch, openAuthXhr } from "./authFetch";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  return authFetch<T>(path, options);
}

export interface UploadProgress {
  loaded: number;
  total: number;
  /** 0..1 fraction; null when total size is not known (rare). */
  fraction: number | null;
  /** True after the bytes have finished sending and we are waiting on the server response. */
  done: boolean;
}

interface AnalyzeOpts {
  currentMedications?: string[];
  onProgress?: (p: UploadProgress) => void;
  signal?: AbortSignal;
}

/**
 * Upload a genome file and start an analysis job, reporting upload progress.
 *
 * Uses XMLHttpRequest because `fetch` does not expose upload progress events
 * on browsers as of 2026. The progress callback fires on every chunk written
 * to the wire, plus once with `done: true` after the body has fully uploaded
 * (the server may still be processing while we await its JSON response).
 */
export function analyzeFile(
  file: File,
  optsOrMeds?: string[] | AnalyzeOpts
): Promise<{ job_id: string; poll_url: string }> {
  const opts: AnalyzeOpts = Array.isArray(optsOrMeds)
    ? { currentMedications: optsOrMeds }
    : (optsOrMeds ?? {});
  const qs =
    opts.currentMedications && opts.currentMedications.length
      ? `?current_medications=${encodeURIComponent(opts.currentMedications.join(","))}`
      : "";

  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);

    const xhr = openAuthXhr("POST", `/analyze${qs}`);

    xhr.upload.onprogress = (e) => {
      if (!opts.onProgress) return;
      opts.onProgress({
        loaded: e.loaded,
        total: e.lengthComputable ? e.total : 0,
        fraction: e.lengthComputable && e.total > 0 ? e.loaded / e.total : null,
        done: false,
      });
    };
    xhr.upload.onload = () => {
      if (!opts.onProgress) return;
      opts.onProgress({
        loaded: file.size,
        total: file.size,
        fraction: 1,
        done: true,
      });
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid server response"));
        }
      } else {
        let message = `HTTP ${xhr.status}`;
        try {
          const body = JSON.parse(xhr.responseText);
          message = body?.detail ?? body?.message ?? message;
        } catch {
          // ignore
        }
        reject(new Error(message));
      }
    };
    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.onabort = () => reject(new Error("Upload cancelled"));

    if (opts.signal) {
      if (opts.signal.aborted) {
        xhr.abort();
        return;
      }
      opts.signal.addEventListener("abort", () => xhr.abort(), { once: true });
    }

    xhr.send(form);
  });
}

/** Fetch the pharmacogenomics profile for a completed job. */
export async function getPGxProfile(jobId: string): Promise<PGxProfile> {
  return apiFetch<PGxProfile>(`/jobs/${jobId}/pgx`);
}

/** Fetch per-drug PGx evidence (CPIC recs, PRS, conformal prediction). */
export async function getDrugDetail(
  jobId: string,
  drug: string
): Promise<DrugDetail> {
  return apiFetch<DrugDetail>(
    `/jobs/${jobId}/drug/${encodeURIComponent(drug)}`
  );
}

/** Fetch the current status (and results when done) of a job. */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return apiFetch<JobStatus>(`/jobs/${jobId}`);
}

/** List recent jobs (status only — no results payload). */
export async function listJobs(
  limit = 50
): Promise<{ jobs: JobListItem[] }> {
  return apiFetch<{ jobs: JobListItem[] }>(`/jobs?limit=${limit}`);
}

/** Curated peptide regulatory status, augmented with live source data. */
export async function getRegulatoryPeptides(
  includeLive = true
): Promise<RegulatoryPeptidesPayload> {
  const qs = includeLive ? "" : "?include_live=false";
  return apiFetch<RegulatoryPeptidesPayload>(`/regulatory/peptides${qs}`);
}

/** Critical regulatory dates, timeline, sources, and live docket comment count. */
export async function getRegulatoryEvents(
  includeLive = true
): Promise<RegulatoryEventsPayload> {
  const qs = includeLive ? "" : "?include_live=false";
  return apiFetch<RegulatoryEventsPayload>(`/regulatory/events${qs}`);
}

// ── Tracking — bridge from /analyze job to a tracking patient ────────────

export interface VariantEvidenceCitation {
  pharmgkb_level: string;
  pmid: string;
  summary: string;
}

export interface VariantCarried {
  rsid: string;
  gene: string;
  genotype: "hom_ref" | "het" | "hom_alt";
  dosage: number;
  evidence: VariantEvidenceCitation | null;
}

export interface PatientFromJobResponse {
  patient: {
    id: string;
    label: string;
    sex: string | null;
    birth_year: number | null;
    notes: string | null;
    created_at: string;
  };
  profile: unknown;
  source: string;
  peptides_with_evidence: string[];
  peptides_with_patient_signal: string[];
  variants_carried: VariantCarried[];
}

/**
 * Create a tracking patient pre-populated with a real-data
 * GeneticProfile derived from a finished /analyze job. The returned
 * payload tells the UI which peptides actually have evidence-based
 * priors for THIS patient's genotypes (vs. the catalog at large),
 * so we can give an honest "we found priors for K of N peptides" line.
 */
export async function createPatientFromJob(
  jobId: string,
  body?: { label?: string; sex?: string; birth_year?: number; notes?: string },
): Promise<PatientFromJobResponse> {
  return apiFetch<PatientFromJobResponse>(`/tracking/patients/from-job/${jobId}`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });
}
