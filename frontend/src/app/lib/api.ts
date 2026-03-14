import type { JobStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "https://flmanbiosci.net/api/v1";

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
  file: File
): Promise<{ job_id: string; poll_url: string }> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<{ job_id: string; poll_url: string }>("/analyze", {
    method: "POST",
    body: form,
  });
}

/** Fetch the current status (and results when done) of a job. */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return apiFetch<JobStatus>(`/jobs/${jobId}`);
}
