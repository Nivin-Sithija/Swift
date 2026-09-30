import { getApiBaseUrl } from "../lib/config";

/** These assert the precedence chain itself, not any one deployment's URL.
    The previous version expected the Render host, which only resolves when an
    uncommitted local `.env` supplies VITE_API_BASE_URL — so it passed on the
    author's machine and failed on every clean checkout and in CI. */
describe("public runtime configuration", () => {
  afterEach(() => {
    delete window.__APP_CONFIG__;
    vi.unstubAllEnvs();
  });

  it("prefers the container runtime API URL over the build-time value", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://built-in.example/api/v1");
    window.__APP_CONFIG__ = { API_BASE_URL: "http://backend:8000/api/v1/" };

    expect(getApiBaseUrl()).toBe("http://backend:8000/api/v1");
  });

  it("falls back to the build-time value when no runtime config is injected", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://swift-gp57.onrender.com/api/v1");
    delete window.__APP_CONFIG__;

    expect(getApiBaseUrl()).toBe("https://swift-gp57.onrender.com/api/v1");
  });

  it("falls back to localhost when neither source is configured", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    delete window.__APP_CONFIG__;

    expect(getApiBaseUrl()).toBe("http://localhost:8000/api/v1");
  });

  it("strips trailing slashes so path joining never double-slashes", () => {
    window.__APP_CONFIG__ = { API_BASE_URL: "http://backend:8000/api/v1///" };

    expect(getApiBaseUrl()).toBe("http://backend:8000/api/v1");
  });
});
