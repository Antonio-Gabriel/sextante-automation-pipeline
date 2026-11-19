import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The backend listens on 127.0.0.1 only (L-07); so does the development server.
const BACKEND = process.env.SEXTANTE_BACKEND_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Only public variables can reach the compiled code; no secret has this prefix (SEC-02).
  envPrefix: "VITE_SEXTANTE_",
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    // Same origin for the browser: /api goes to the backend, so no CORS (SEC-11).
    proxy: { "/api": { target: BACKEND, changeOrigin: false } },
  },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    css: false,
  },
});
