// SPDX-License-Identifier: MIT
/**
 * Static, dependency-free visualization used when motion is reduced, WebGL is
 * unavailable, or the 3D chunk is still loading. It conveys the same metric —
 * a growing forest — with an inline SVG hill plus emoji trees, fully labelled
 * for assistive tech. Zero binary assets; pure markup.
 */

import { KG_PER_TREE, treeCountForSaved } from "./savingsModel";
import { EMOJI } from "../../shared/ui/emojiMap";

interface SavingsFallbackProps {
  savedKg: number;
  loading?: boolean;
}

const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 1,
});

export function SavingsFallback({ savedKg, loading = false }: SavingsFallbackProps) {
  const trees = treeCountForSaved(savedKg);
  const description =
    trees === 0
      ? "No savings logged yet — your forest is waiting to grow."
      : `A forest of ${trees} ${trees === 1 ? "tree" : "trees"} for ${numberFormat.format(
          savedKg,
        )} kg of CO2 avoided (about ${KG_PER_TREE} kg per tree).`;

  return (
    <figure className="savings-fallback">
      <svg
        className="savings-fallback-svg"
        viewBox="0 0 320 160"
        role="img"
        aria-label={description}
      >
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#bfe3cf" />
            <stop offset="100%" stopColor="#eef6f0" />
          </linearGradient>
        </defs>
        <rect width="320" height="160" fill="url(#sky)" />
        <ellipse cx="160" cy="170" rx="200" ry="60" fill="#0f6b46" opacity="0.85" />
      </svg>

      <div className="savings-fallback-trees" aria-hidden="true">
        {Array.from({ length: Math.min(trees, 24) }, (_, index) => (
          <span key={index} className="fallback-tree">
            {index % 4 === 0 ? EMOJI.sprout : EMOJI.tree}
          </span>
        ))}
      </div>

      <figcaption>
        {loading ? "Preparing your 3D forest… " : null}
        {description}
      </figcaption>
    </figure>
  );
}
