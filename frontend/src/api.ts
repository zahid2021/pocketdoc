const TOKEN_KEY = "pocketdoc_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T = any>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(path, { ...options, headers });
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : "Something went wrong";
    throw new ApiError(res.status, message);
  }
  return data as T;
}

export function waitLabel(seconds: number) {
  const s = Math.max(0, Math.round(seconds));
  if (s <= 5) return "Now";
  if (s < 600) {
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}:${String(r).padStart(2, "0")}`;
  }
  return `${Math.ceil(s / 60)} min`;
}

export function statusLabel(status: string) {
  const map: Record<string, string> = {
    waiting: "Waiting",
    checked_in: "Checked in",
    in_consultation: "In Consultation",
    completed: "Completed",
    cancelled: "Cancelled",
    no_show: "No-show",
    not_started: "Not started",
    running: "Running",
    paused: "Paused",
  };
  return map[status] || status;
}

export const CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan"];
