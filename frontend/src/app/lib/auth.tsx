"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  authFetch,
  clearStoredToken,
  getToken,
  setStoredToken,
} from "./authFetch";

interface AuthUser {
  id: string;
  username: string;
  created_at: string;
}

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  token: null,
  user: null,
  loading: false,
  login: async () => {},
  logout: async () => {},
});

interface LoginResponse {
  token: string;
  expires_at: string;
  user: AuthUser;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, hydrate from localStorage and verify the token via /auth/me.
  // A stale or revoked token causes authFetch to clear it and redirect,
  // so we only have to handle the happy path here. setState calls are
  // pushed into async callbacks so this effect doesn't trigger a
  // cascading synchronous re-render on mount.
  useEffect(() => {
    const stored = getToken();
    if (!stored) {
      Promise.resolve().then(() => setLoading(false));
      return;
    }
    Promise.resolve()
      .then(() => setTokenState(stored))
      .then(() => authFetch<{ user: AuthUser | null; via: string }>("/auth/me"))
      .then((res) => setUser(res.user))
      .catch(() => {
        // authFetch already cleared+redirected on 401; on other errors,
        // assume offline and keep the token cached.
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const body = await authFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setStoredToken(body.token);
    setTokenState(body.token);
    setUser(body.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authFetch<{ revoked: boolean }>("/auth/logout", { method: "POST" });
    } catch {
      // ignore — even if the network call fails we still want to clear
      // local state and bounce to /login.
    }
    clearStoredToken();
    setTokenState(null);
    setUser(null);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
