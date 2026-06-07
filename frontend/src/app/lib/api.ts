import type { JobStatus, JobListItem, PGxProfile, DrugDetail } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://flmanbiosci.net/api/v1";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? body?.message ?? message;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

/** Upload a genome file and start an analysis job. */
export async function analyzeFile(
  file: File,
  currentMedications?: string[]
): Promise<{ job_id: string; poll_url: string }> {
  const form = new FormData();
  form.append("file", file);
  const qs =
    currentMedications && currentMedications.length
      ? `?current_medications=${encodeURIComponent(currentMedications.join(","))}`
      : "";
  return apiFetch<{ job_id: string; poll_url: string }>(`/analyze${qs}`, {
    method: "POST",
    body: form,
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
