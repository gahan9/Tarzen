// SPDX-License-Identifier: MIT
// Augment vitest's matcher types with the accessibility matcher registered in
// `setup.ts`, so `expect(...).toHaveNoViolations()` type-checks.
import type { AxeMatchers } from "vitest-axe/matchers";

declare module "vitest" {
  /* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
  interface Assertion<T = any> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
  /* eslint-enable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
}
