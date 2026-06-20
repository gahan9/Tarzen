// SPDX-License-Identifier: MIT
/**
 * Global test setup: register Testing Library DOM matchers and the
 * accessibility (`toHaveNoViolations`) matcher, and clean up the DOM between
 * tests. Imported by every test via `vite.config.ts` `setupFiles`.
 */

import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, expect } from "vitest";
import * as axeMatchers from "vitest-axe/matchers";

// vitest-axe's auto extend-expect targets an older vitest; register the
// matchers explicitly so `toHaveNoViolations` works under vitest 2.x.
expect.extend(axeMatchers);

afterEach(() => {
  cleanup();
});
