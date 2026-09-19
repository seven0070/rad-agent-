/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RAD_API?: string;
  readonly VITE_RAD_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
