// SPDX-License-Identifier: MIT
/**
 * Pure mapping from avoided CO2 to a tree count, shared by the 3D scene and the
 * static fallback so both tell the same story. The upper bound keeps the scene
 * within the draw-call / triangle budget on low-end devices.
 */

/** Roughly the CO2 a young tree sequesters per year — an intuitive unit. */
export const KG_PER_TREE = 5;

/** Hard cap on rendered trees to protect the frame budget on weak GPUs. */
export const MAX_TREES = 60;

/** Trees to render for a given saving (>= 1 once any saving exists). */
export function treeCountForSaved(savedKg: number): number {
  if (savedKg <= 0) return 0;
  const raw = Math.round(savedKg / KG_PER_TREE);
  return Math.max(1, Math.min(MAX_TREES, raw));
}
