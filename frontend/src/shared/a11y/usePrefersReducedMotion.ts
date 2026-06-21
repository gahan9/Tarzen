// SPDX-License-Identifier: MIT
/**
 * Tracks the user's `prefers-reduced-motion` setting reactively.
 *
 * The 3D visualization uses this to swap to a calm, static fallback rather than
 * running auto-rotation or camera motion — a hard requirement from the
 * immersive-3d-ux skill (motion comfort + accessibility).
 */

import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function getInitial(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia(QUERY).matches;
}

export function usePrefersReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState<boolean>(getInitial);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const media = window.matchMedia(QUERY);
    const onChange = (event: MediaQueryListEvent) => {
      setPrefersReduced(event.matches);
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  return prefersReduced;
}
