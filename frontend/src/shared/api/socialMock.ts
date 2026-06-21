// SPDX-License-Identifier: MIT
/**
 * Local mocks for the savings and social endpoints, gated by
 * `VITE_USE_MOCK_API`. Numbers are illustrative (rule-based) and mirror the
 * backend contract field-for-field so the UI can be exercised end-to-end
 * without a live backend. Not authoritative — the backend owns real scoring.
 */

import {
  type CarpoolImportRow,
  type LeaderboardResponse,
  type LeaderboardScope,
  type ProfileResponse,
  type SavingsImportResponse,
  type SavingsRequest,
  type SavingsResponse,
  type TicketResponse,
} from "@carbon/shared-types";

import { newTraceId } from "../telemetry/trace";

/** Illustrative per-km factors (kg CO2e per passenger-km). Not authoritative. */
const CAR_FACTOR = 0.171;
const TRANSIT_FACTOR: Record<"bus" | "rail", number> = {
  bus: 0.103,
  rail: 0.041,
};

const VERIFICATION_BONUS = 15;
const BASE_POINTS = 10;

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

/** Avoided emissions vs driving the same distance solo, clamped at >= 0. */
function savedFor(
  mode: SavingsRequest["mode"],
  distanceKm: number,
  passengers: number,
): number {
  if (mode === "carpool") {
    const occupants = Math.max(passengers, 1);
    return Math.max(0, CAR_FACTOR * distanceKm * (1 - 1 / occupants));
  }
  return Math.max(0, (CAR_FACTOR - TRANSIT_FACTOR[mode]) * distanceKm);
}

export function mockSavings(request: SavingsRequest): SavingsResponse {
  const saved = savedFor(request.mode, request.distance_km, request.passengers ?? 1);
  const verified = request.source === "ticket";
  return {
    kg_co2e_saved: round2(saved),
    verified,
    points_awarded: BASE_POINTS + (verified ? VERIFICATION_BONUS : 0),
    badges_unlocked: saved > 5 ? ["bronze"] : [],
    streak_days: 1,
    request_id: newTraceId(),
  };
}

export function mockImport(rows: CarpoolImportRow[]): SavingsImportResponse {
  const total = rows.reduce(
    (sum, row) => sum + savedFor("carpool", row.distance_km, row.passengers),
    0,
  );
  return {
    total_kg_co2e_saved: round2(total),
    rows_imported: rows.length,
    points_awarded: BASE_POINTS * rows.length,
    badges_unlocked: total > 20 ? ["silver"] : [],
    request_id: newTraceId(),
  };
}

export function mockTicket(): TicketResponse {
  const saved = savedFor("rail", 32, 1);
  return {
    kg_co2e_saved: round2(saved),
    verified: true,
    points_awarded: BASE_POINTS + VERIFICATION_BONUS,
    badges_unlocked: ["verified_rider"],
    streak_days: 3,
    request_id: newTraceId(),
    extraction: {
      origin: "Central Station",
      destination: "Riverside",
      mode: "rail",
      date: "2026-06-20",
      fare: 3.4,
    },
  };
}

const MOCK_HANDLES: ReadonlyArray<readonly [string, string, number]> = [
  ["SwiftFox-4821", "\u{1F98A}", 1280],
  ["CalmOwl-1147", "\u{1F989}", 1042],
  ["BoldOtter-9920", "\u{1F9A6}", 870],
  ["KeenDeer-3055", "\u{1F98C}", 645],
  ["BrightHawk-7781", "\u{1F985}", 510],
  ["MildWolf-2298", "\u{1F43A}", 333],
];

export function mockLeaderboard(scope: LeaderboardScope): LeaderboardResponse {
  const entries = MOCK_HANDLES.map(([anon_handle, emoji, score], index) => ({
    anon_handle,
    emoji,
    score,
    rank: index + 1,
    is_me: index === 3,
  }));
  return {
    scope,
    region: scope === "region" ? "IN" : null,
    entries,
    my_rank: 4,
    percentile: 62,
    tips: [
      "Log a carpool trip this week to climb past the rider above you.",
      "Verified tickets earn a bonus — upload one to widen your lead.",
      "Keep a daily streak going for compounding bonus points.",
    ],
  };
}

export function mockProfile(): ProfileResponse {
  return {
    anon_handle: "KeenDeer-3055",
    emoji: "\u{1F98C}",
    region: "IN",
    points: 645,
    streak_days: 5,
    badges: ["bronze", "week_warrior"],
    total_kg_co2e_saved: 128.6,
    my_rank: 4,
    percentile: 62,
  };
}
