const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "pairup.access-token";
const REFRESH_TOKEN_KEY = "pairup.refresh-token";

type ApiFetchOptions = RequestInit & {
  auth?: boolean;
};

export function saveAuthTokens(access: string, refresh: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearAuthTokens() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAccessToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getAdminUrl() {
  return `${API_BASE_URL.replace(/\/api\/v1\/?$/, "")}/admin/`;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const resolvedHeaders = new Headers(headers);
  resolvedHeaders.set("Content-Type", "application/json");

  if (auth) {
    const accessToken = getAccessToken();
    if (accessToken) {
      resolvedHeaders.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}/${path.replace(/^\//, "")}`, {
    ...rest,
    headers: resolvedHeaders,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Request failed.";
    throw new Error(detail);
  }

  return data as T;
}
