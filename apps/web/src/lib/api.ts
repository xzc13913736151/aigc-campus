const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");

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

function getPayloadKeys(body: BodyInit | null | undefined): string[] | undefined {
  if (!body) {
    return undefined;
  }

  if (typeof body === "string") {
    try {
      const parsed = JSON.parse(body);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return Object.keys(parsed);
      }
    } catch {
      return undefined;
    }
  }

  if (typeof FormData !== "undefined" && body instanceof FormData) {
    return Array.from(body.keys());
  }

  if (typeof URLSearchParams !== "undefined" && body instanceof URLSearchParams) {
    return Array.from(body.keys());
  }

  return undefined;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const resolvedHeaders = new Headers(headers);
  resolvedHeaders.set("Content-Type", "application/json");
  const url = `${API_BASE_URL}/${path.replace(/^\//, "")}`;
  const payloadKeys = getPayloadKeys(rest.body);

  if (auth) {
    const accessToken = getAccessToken();
    if (accessToken) {
      resolvedHeaders.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  console.debug("[apiFetch] dispatch", {
    url,
    method: rest.method ?? "GET",
    auth,
    payloadKeys,
  });

  let response: Response;
  try {
    response = await fetch(url, {
      ...rest,
      headers: resolvedHeaders,
    });
  } catch (error) {
    console.error("[apiFetch] network error", {
      url,
      method: rest.method ?? "GET",
      auth,
      payloadKeys,
      error,
      stack: error instanceof Error ? error.stack : undefined,
    });
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const responseText = await response.text();
  let data: unknown = {};
  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch {
      data = {};
    }
  }

  if (!response.ok) {
    console.error("[apiFetch] response error", {
      url,
      method: rest.method ?? "GET",
      status: response.status,
      statusText: response.statusText,
      payloadKeys,
      body: responseText,
    });

    const detail =
      typeof (data as { detail?: unknown })?.detail === "string"
        ? (data as { detail: string }).detail
        : `Request failed with ${response.status} ${response.statusText}.`;
    throw new Error(detail);
  }

  console.debug("[apiFetch] response ok", {
    url,
    method: rest.method ?? "GET",
    status: response.status,
  });

  return data as T;
}
