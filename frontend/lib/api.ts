const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function showApiError(type: "error" | "warning" | "info", message: string) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(
      new CustomEvent("show-toast", {
        detail: { type, message },
      })
    );
  }
}

async function buildApiError(res: Response, method: string, path: string): Promise<Error> {
  let detail = "";
  try {
    const data = await res.json();
    detail = data?.detail ? `: ${String(data.detail)}` : "";
  } catch {
    detail = "";
  }
  return new Error(`${method} ${path} failed (${res.status})${detail}`);
}

export async function apiGet<T>(path: string, showErrorToast: boolean = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const error = await buildApiError(res, "GET", path);
    if (showErrorToast) {
      showApiError("error", error.message);
    }
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown, showErrorToast: boolean = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const error = await buildApiError(res, "POST", path);
    if (showErrorToast) {
      showApiError("error", error.message);
    }
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function apiPut<T>(path: string, body: unknown, showErrorToast: boolean = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const error = await buildApiError(res, "PUT", path);
    if (showErrorToast) {
      showApiError("error", error.message);
    }
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function apiDelete<T>(path: string, showErrorToast: boolean = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const error = await buildApiError(res, "DELETE", path);
    if (showErrorToast) {
      showApiError("error", error.message);
    }
    throw error;
  }
  return res.json() as Promise<T>;
}
