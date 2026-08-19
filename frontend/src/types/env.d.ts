/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_NAME?: string;
  readonly VITE_DEFAULT_THEME?: string;
  readonly VITE_USE_MOCK_API?: string;
  readonly VITE_DEVELOPMENT_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  __APP_CONFIG__?: {
    API_BASE_URL?: string;
  };
}
