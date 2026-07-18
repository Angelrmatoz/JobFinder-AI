import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { configDefaults } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: "./postcss.config.js",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
    exclude: [...configDefaults.exclude, "src/e2e/**"],
  },
});
