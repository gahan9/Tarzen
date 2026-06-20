// SPDX-License-Identifier: MIT
/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    // Resolve the workspace contract from source so unit tests do not depend on
    // a prior `dist` build of the shared-types package.
    alias: {
      "@carbon/shared-types": fileURLToPath(
        new URL("../packages/shared-types/src/index.ts", import.meta.url),
      ),
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      // Scope the gate to the unit-tested surface: pure logic and presentational
      // components. Networked auth/Firebase wiring and the app shell are covered
      // by integration/Lighthouse, not these unit thresholds.
      include: [
        "src/shared/telemetry/**",
        "src/shared/api/mock.ts",
        "src/shared/api/errors.ts",
        "src/shared/a11y/**",
        "src/features/insights/**",
        "src/features/footprint/FootprintForm.tsx",
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 90,
        statements: 90,
      },
    },
  },
});
