// SPDX-License-Identifier: MIT
/**
 * Profile page: the signed-in user's anonymised identity and progress — handle,
 * region, points, streak, badges, and lifetime CO2 avoided — plus a
 * size-conscious 3D visualization of that saving. The heavy Three.js scene is
 * code-split and only loaded when motion is allowed and WebGL is available;
 * otherwise a static emoji/SVG fallback renders instead.
 */

import { Suspense, lazy, useCallback, useEffect } from "react";
import {
  BADGE_LABELS,
  type ProfileResponse,
} from "@carbon/shared-types";

import { getProfile } from "../../shared/api/socialClient";
import { useAsyncFn } from "../../shared/hooks/useAsyncFn";
import { useAuth } from "../../shared/auth/useAuth";
import { usePrefersReducedMotion } from "../../shared/a11y/usePrefersReducedMotion";
import { isWebglAvailable } from "../../shared/ui/webgl";
import { Emoji } from "../../shared/ui/Emoji";
import { emojiForBadge, emojiForHandle } from "../../shared/ui/emojiMap";
import { SavingsFallback } from "../visualization/SavingsFallback";

// Code-split: `three` + the R3F scene land in a separate async chunk that is
// only fetched when we actually mount the canvas.
const SavingsScene = lazy(() => import("../visualization/SavingsScene"));

const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 1,
});

function badgeLabel(badgeId: string): string {
  return (
    BADGE_LABELS[badgeId] ??
    badgeId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function ProfileStats({ profile }: { profile: ProfileResponse }) {
  return (
    <>
      <header className="profile-identity">
        <span className="profile-emoji" aria-hidden="true">
          {emojiForHandle(profile.anon_handle, profile.emoji)}
        </span>
        <div>
          <h1 id="profile-heading">{profile.anon_handle}</h1>
          {profile.region ? (
            <p className="profile-region">
              <Emoji name="region" /> Region: {profile.region}
            </p>
          ) : null}
        </div>
      </header>

      <dl className="profile-stats">
        <div className="stat">
          <dt>
            <Emoji name="points" /> Points
          </dt>
          <dd>{numberFormat.format(profile.points)}</dd>
        </div>
        <div className="stat">
          <dt>
            <Emoji name="streak" /> Streak
          </dt>
          <dd>{profile.streak_days} days</dd>
        </div>
        <div className="stat">
          <dt>
            <Emoji name="sprout" /> CO2 avoided
          </dt>
          <dd>{numberFormat.format(profile.total_kg_co2e_saved)} kg</dd>
        </div>
        {profile.my_rank != null ? (
          <div className="stat">
            <dt>
              <Emoji name="trophy" /> Rank
            </dt>
            <dd>#{profile.my_rank}</dd>
          </div>
        ) : null}
      </dl>

      {profile.badges.length > 0 ? (
        <section aria-labelledby="profile-badges-heading">
          <h2 id="profile-badges-heading">Badges</h2>
          <ul className="badge-list">
            {profile.badges.map((badge) => (
              <li key={badge} className="badge-chip">
                <Emoji name={emojiForBadge(badge)} /> {badgeLabel(badge)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </>
  );
}

export function ProfilePage() {
  const { getIdToken } = useAuth();
  const prefersReducedMotion = usePrefersReducedMotion();

  const { state, run } = useAsyncFn(
    useCallback(
      (signal: AbortSignal) => getProfile({ signal, getToken: getIdToken }),
      [getIdToken],
    ),
  );

  useEffect(() => {
    void run();
  }, [run]);

  if (state.status === "loading" || state.status === "idle") {
    return (
      <p className="result-loading" role="status">
        Loading your profile…
      </p>
    );
  }

  if (state.status === "error") {
    return (
      <p role="alert" className="field-error">
        {state.message}
      </p>
    );
  }

  const profile = state.data;
  const savedKg = profile.total_kg_co2e_saved;
  const animate = !prefersReducedMotion && isWebglAvailable();

  return (
    <section aria-labelledby="profile-heading" className="profile-page">
      <ProfileStats profile={profile} />

      <section aria-labelledby="viz-heading" className="viz-section">
        <h2 id="viz-heading">
          <Emoji name="tree" /> Your forest of avoided emissions
        </h2>
        <p className="form-hint">
          Each tree represents roughly 5 kg of CO2 you&apos;ve kept out of the air.
        </p>
        {animate ? (
          <Suspense fallback={<SavingsFallback savedKg={savedKg} loading />}>
            <SavingsScene savedKg={savedKg} />
          </Suspense>
        ) : (
          <SavingsFallback savedKg={savedKg} />
        )}
      </section>
    </section>
  );
}
