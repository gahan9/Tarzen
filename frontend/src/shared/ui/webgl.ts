// SPDX-License-Identifier: MIT
/**
 * Best-effort WebGL capability probe.
 *
 * Used to decide whether to mount the Three.js scene at all. If WebGL is
 * unavailable (old device, disabled, blocked) we render the static emoji/SVG
 * fallback instead of a broken `<canvas>` — "degrade, never break".
 */

let cached: boolean | null = null;

export function isWebglAvailable(): boolean {
  if (cached !== null) return cached;
  if (typeof document === "undefined") {
    cached = false;
    return cached;
  }
  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl") ?? canvas.getContext("experimental-webgl");
    cached = Boolean(gl);
  } catch {
    cached = false;
  }
  return cached;
}
