const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

/** Read at call time, not module load: `runtime-config.js` lets a container
    override the API host after the bundle is built. */
export function getApiBaseUrl(): string {
  return (
    window.__APP_CONFIG__?.API_BASE_URL?.trim() ||
    import.meta.env.VITE_API_BASE_URL?.trim() ||
    DEFAULT_API_BASE_URL
  ).replace(/\/+$/, "");
}

export const getAppName = (): string =>
  import.meta.env.VITE_APP_NAME?.trim() || "Swift";

export const isDevelopmentMode = (): boolean =>
  import.meta.env.VITE_DEVELOPMENT_MODE?.trim().toLowerCase() === "true";
