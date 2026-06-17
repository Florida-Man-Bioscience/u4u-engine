/**
 * Shared API transport layer.
 *
 * Thin wrapper around fetch + XMLHttpRequest that prefixes paths with the
 * configured API base and normalises error handling. Auth lives upstream:
 * the deploy stack puts an Authentik forward-auth proxy in front of the
 * api, so requests from the browser carry no credentials of their own —
 * the proxy stamps trusted X-Authentik-* headers before the api sees the
 * request. The frontend just hits relative paths.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

/**
 * Drop-in replacement for `fetch` that prefixes the API base and throws
 * on non-OK responses, preserving the server's `detail` message when
 * present.
 */
export async function authFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  // Default JSON content-type for body-carrying requests; callers can
  // override (or set to undefined for multipart).
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = await res.json();
      detail = body?.detail ?? body?.message;
    } catch {
      // ignore
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/**
 * XHR open helper for upload paths that need progress events. The caller
 * is responsible for setting onload/onerror/etc. and calling send.
 */
export function openAuthXhr(method: string, path: string): XMLHttpRequest {
  const xhr = new XMLHttpRequest();
  xhr.open(method, `${API_BASE}${path}`);
  return xhr;
}
