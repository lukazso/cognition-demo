import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@platform": path.resolve(__dirname, "../../../platform/frontend"),
    },
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
