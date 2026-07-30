const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export function getApiBaseUrl(): string {
  return (
    window.__APP_CONFIG__?.API_BASE_URL?.trim() ||
    import.meta.env.VITE_API_BASE_URL?.trim() ||
    DEFAULT_API_BASE_URL
  ).replace(/\/+$/, "");
}

export const publicConfig = Object.freeze({
  apiBaseUrl: getApiBaseUrl(),
  appName: import.meta.env.VITE_APP_NAME?.trim() || "Swift",
});
