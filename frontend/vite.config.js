import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/run": "http://localhost:8000", "/status": "http://localhost:8000", "/emails": "http://localhost:8000" } },
});
