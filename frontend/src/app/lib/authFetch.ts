/**
 * Shared authenticated transport layer.
 *
 * Every API call in the app goes through this module so that
 *
 *   - the bearer token is attached in one place (no per-page boilerplate);
 *   - a 401 from the server clears the stored token and redirects to
 *     /login from one place (so token expiry doesn't manifest as a
 *     thousand confusing error states across pages);
 *   - file uploads, which use XMLHttpRequest for progress reporting,
 *     share the same auth behaviour as the regular fetch calls.
 *
 * The token is stored in localStorage under TOKEN_KEY. Non-React code
 * (this file, the XHR helper) reads it directly from there so it doesn't
 * need to pull in React context.
 */

export const TOKEN_KEY = "u4u_token";
export const LOGIN_PATH = "/login";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://app.flmanbiosci.net/api/v1";

// Build-time escape hatch — when NEXT_PUBLIC_AUTH_DISABLED=1 is passed in,
// 401 responses do NOT clear the token or bounce to /login. Used together
// with the backend's ALLOW_INSECURE_NO_AUTH=1 so demo deploys are open.
const AUTH_DISABLED = process.env.NEXT_PUBLIC_AUTH_DISABLED === "1";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

/**
 * Redirect to /login, preserving where the user was so we can send them
 * back after a successful sign-in. Safe to call multiple times — the
 * second call is a no-op because the browser is already navigating.
 */
function redirectToLogin() {
  if (AUTH_DISABLED) return;
  if (typeof window === "undefined") return;
  if (window.location.pathname.startsWith(LOGIN_PATH)) return;
  const next = encodeURIComponent(
    window.location.pathname + window.location.search,
  );
  window.location.href = `${LOGIN_PATH}?next=${next}`;
}

/**
 * Drop-in replacement for `fetch` that attaches the bearer token and
 * funnels 401s into the login redirect. Throws on non-OK responses,
 * preserving the server's `detail` message when present.
 */
export async function authFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  // Default JSON content-type for body-carrying requests; callers can
  // override (or set to undefined for multipart).
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (res.status === 401) {
    clearStoredToken();
    redirectToLogin();
    throw new Error("Session expired — please sign in again.");
  }

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
 * XHR open helper for upload paths that need progress events. Attaches
 * the bearer token and, on 401, performs the same clear+redirect. The
 * caller is responsible for setting onload/onerror/etc. and calling send.
 */
export function openAuthXhr(method: string, path: string): XMLHttpRequest {
  const xhr = new XMLHttpRequest();
  xhr.open(method, `${API_BASE}${path}`);
  const token = getToken();
  if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  // Wrap onreadystatechange to catch 401s before user code reacts.
  xhr.addEventListener("readystatechange", () => {
    if (xhr.readyState === 4 && xhr.status === 401) {
      clearStoredToken();
      redirectToLogin();
    }
  });
  return xhr;
}
