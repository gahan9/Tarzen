// SPDX-License-Identifier: MIT
/**
 * Lightweight trace-id helper.
 *
 * Each outbound API call carries an `X-Trace-Id` header so a request can be
 * correlated across web -> API -> Gemini -> functions (see plan: SLO/trace
 * propagation). We generate a client-side id when one is not supplied.
 */

const TRACE_HEADER = "X-Trace-Id";

/** Generates a RFC-4122 v4 id, falling back when `crypto.randomUUID` is absent. */
export function newTraceId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback for older runtimes / non-secure contexts.
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const rand = (Math.random() * 16) | 0;
    const value = char === "x" ? rand : (rand & 0x3) | 0x8;
    return value.toString(16);
  });
}

export { TRACE_HEADER };
