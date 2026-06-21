// SPDX-License-Identifier: MIT
/**
 * Unified success card for any savings write (manual, import, or ticket).
 * Shows avoided CO2, points awarded, verification state, and any newly
 * unlocked badges — each emoji decorated with an adjacent text label.
 */

import { forwardRef } from "react";
import { BADGE_LABELS } from "@carbon/shared-types";

import { Emoji } from "../../shared/ui/Emoji";
import { emojiForBadge } from "../../shared/ui/emojiMap";

export interface SavingsSummary {
  title: string;
  kgSaved: number;
  pointsAwarded: number;
  verified: boolean;
  badgesUnlocked: string[];
}

const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2,
});

function badgeLabel(badgeId: string): string {
  return (
    BADGE_LABELS[badgeId] ??
    badgeId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export const SavingsResultCard = forwardRef<HTMLElement, { summary: SavingsSummary }>(
  function SavingsResultCard({ summary }, ref) {
    return (
      <section
        ref={ref}
        tabIndex={-1}
        aria-labelledby="savings-result-heading"
        className="insight-card savings-result"
      >
        <h2 id="savings-result-heading">
          <Emoji name="sprout" /> {summary.title}
        </h2>

        <p className="insight-total">
          <span className="insight-total-value">
            {numberFormat.format(summary.kgSaved)}
          </span>{" "}
          <span className="insight-total-unit">kg CO2e avoided</span>
        </p>

        <p className="savings-points">
          <Emoji name="points" /> +{summary.pointsAwarded} points
          {summary.verified ? (
            <>
              {" "}
              <Emoji name="verified" label="Verified" /> verified
            </>
          ) : null}
        </p>

        {summary.badgesUnlocked.length > 0 ? (
          <div className="savings-badges" role="group" aria-label="Badges unlocked">
            <h3>New badges</h3>
            <ul className="badge-list">
              {summary.badgesUnlocked.map((badge) => (
                <li key={badge} className="badge-chip">
                  <Emoji name={emojiForBadge(badge)} /> {badgeLabel(badge)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
    );
  },
);
