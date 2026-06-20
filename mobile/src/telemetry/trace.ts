// SPDX-License-Identifier: MIT
/**
 * Lightweight trace-id helper (mirrors the web app's telemetry contract).
 *
 * Each outbound API call carries an `X-Trace-Id` header so a request can be
 * correlated across mobile -> API -> Gemini -> functions. We generate a
 * client-side id when one is not supplied. The same value also seeds offline
 * log `clientId`s so a queued entry keeps a stable identity across retries.
 */

const TRACE_HEADER = "X-Trace-Id";

/** Generates an RFC-4122 v4 id, falling back when `crypto.randomUUID` is absent. */
export function newTraceId(): string {
  const globalCrypto = (globalThis as { crypto?: Crypto }).crypto;
  if (globalCrypto && typeof globalCrypto.randomUUID === "function") {
    return globalCrypto.randomUUID();
  }
  // Fallback for runtimes without a secure crypto (older RN JS engines).
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const rand = (Math.random() * 16) | 0;
    const value = char === "x" ? rand : (rand & 0x3) | 0x8;
    return value.toString(16);
  });
}

export { TRACE_HEADER };
