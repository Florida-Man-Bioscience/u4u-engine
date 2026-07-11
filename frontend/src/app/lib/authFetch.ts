/**
 * Shared API transport layer.
 *
 * Thin wrapper around fetch + XMLHttpRequest that prefixes paths with the
 * configured API base and normalises error handling. Historically auth
 * lived entirely upstream (an Authentik forward-auth proxy stamping
 * trusted X-Authentik-* headers), so requests carried no credentials of
 * their own. The backend now also accepts an end-user OIDC Bearer access
 * token (`engine/users/`); the SPA login/token-store UI that would obtain
 * one is a follow-on task blocked on a real Authentik instance being
 * provisioned (see CLAUDE.md). Until then `getAccessToken()` always
 * returns null and every request stays unauthenticated, same as today —
 * this is just the non-breaking scaffold that later work fills in.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

/**
 * In-memory access-token accessor. Returns null until the OIDC login flow
 * (deferred) installs a real token store. Kept as a plain function (not a
 * module-level variable) so that filling it in later doesn't require
 * touching every call site.
 */
export function getAccessToken(): string | null {
  return null;
}

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
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
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
  const token = getAccessToken();
  if (token) {
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  }
  return xhr;
}
