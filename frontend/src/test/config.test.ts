import { getApiBaseUrl } from "../lib/config";

describe("public runtime configuration", () => {
  it("prefers the container runtime API URL", () => {
    window.__APP_CONFIG__ = {
      API_BASE_URL: "http://backend:8000/api/v1/",
    };

    expect(getApiBaseUrl()).toBe("http://backend:8000/api/v1");
  });

  it("uses a safe development fallback when runtime configuration is absent", () => {
    delete window.__APP_CONFIG__;

    expect(getApiBaseUrl()).toBe("http://localhost:8000/api/v1");
  });
});
