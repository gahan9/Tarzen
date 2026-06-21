// SPDX-License-Identifier: MIT
/**
 * Shared API contract for the Carbon Footprint Platform.
 *
 * This module is the single source of truth for the request/response shapes
 * exchanged with `POST /api/footprint`. Both the web app and the mobile app
 * import the zod schemas (for runtime validation) and the inferred TypeScript
 * types (for compile-time safety) from here. Keep this file in lock-step with
 * the backend Pydantic models — it is a contract, not an implementation detail.
 */

import { z } from "zod";

/** Domains the platform can track. Only `transport` is live for the MVP. */
export const DOMAINS = ["transport"] as const;
export const domainSchema = z.enum(DOMAINS);
export type Domain = z.infer<typeof domainSchema>;

/** Transport modes supported by the footprint engine. */
export const TRANSPORT_MODES = ["car", "bus", "rail", "flight"] as const;
export const transportModeSchema = z.enum(TRANSPORT_MODES);
export type TransportMode = z.infer<typeof transportModeSchema>;

/**
 * Request body for `POST /api/footprint`.
 *
 * Bounds mirror the backend field validation (non-negative, sane upper limits)
 * so the client rejects bad input before a network round-trip.
 */
export const footprintRequestSchema = z.object({
  domain: domainSchema,
  mode: transportModeSchema,
  distance_km: z
    .number({ invalid_type_error: "Distance must be a number." })
    .positive("Distance must be greater than zero.")
    .max(40_075, "Distance cannot exceed the Earth's circumference."),
  passengers: z
    .number({ invalid_type_error: "Passengers must be a number." })
    .int("Passengers must be a whole number.")
    .min(1, "There must be at least one passenger.")
    .max(1_000, "Passengers exceeds a sane upper limit.")
    .optional(),
});
export type FootprintRequest = z.infer<typeof footprintRequestSchema>;

/** One line item contributing to the total footprint. */
export const breakdownItemSchema = z.object({
  label: z.string(),
  kg_co2e: z.number(),
});
export type BreakdownItem = z.infer<typeof breakdownItemSchema>;

/** Empathetic, policy-gated insight returned alongside the calculation. */
export const insightSchema = z.object({
  message: z.string(),
  benchmark: z.string(),
  actions: z.array(z.string()),
  needs_context: z.boolean(),
  llm_used: z.boolean(),
});
export type Insight = z.infer<typeof insightSchema>;

/** Successful response body for `POST /api/footprint`. */
export const footprintResponseSchema = z.object({
  kg_co2e: z.number(),
  breakdown: z.array(breakdownItemSchema),
  insight: insightSchema,
  request_id: z.string(),
});
export type FootprintResponse = z.infer<typeof footprintResponseSchema>;

/** Typed error envelope used by every non-2xx API response. */
export const errorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    request_id: z.string(),
  }),
});
export type ErrorEnvelope = z.infer<typeof errorEnvelopeSchema>;

/**
 * Human-readable labels for transport modes. Centralised here so web and
 * mobile render identical copy. Exhaustively keyed by {@link TransportMode}.
 */
export const TRANSPORT_MODE_LABELS: Record<TransportMode, string> = {
  car: "Car",
  bus: "Bus",
  rail: "Rail",
  flight: "Flight",
};

/* ---------------------------------------------------------------------------
 * Carbon savings (avoided emissions vs a solo-car baseline).
 *
 * `saved = baseline_solo_car - actual`, clamped at >= 0. These contracts back
 * the `POST /api/savings*` endpoints. Unknown keys are stripped by zod, so the
 * backend may add fields without breaking the client; only the fields marked
 * required below must be present.
 * ------------------------------------------------------------------------- */

/** How a savings record was captured (anti-cheat: `ticket` implies verified). */
export const SAVINGS_SOURCES = ["manual", "import", "ticket"] as const;
export const savingsSourceSchema = z.enum(SAVINGS_SOURCES);
export type SavingsSource = z.infer<typeof savingsSourceSchema>;

/**
 * Low-carbon mode that produced the saving:
 *  - `carpool` — sharing a car: `car_factor * distance * (1 - 1/passengers)`.
 *  - `bus` / `rail` — transit instead of solo car: `(car_factor - transit) * d`.
 */
export const SAVINGS_MODES = ["carpool", "bus", "rail"] as const;
export const savingsModeSchema = z.enum(SAVINGS_MODES);
export type SavingsMode = z.infer<typeof savingsModeSchema>;

/** Request body for `POST /api/savings` (manual or single carpool entry). */
export const savingsRequestSchema = z
  .object({
    source: savingsSourceSchema,
    mode: savingsModeSchema,
    distance_km: z
      .number({ invalid_type_error: "Distance must be a number." })
      .positive("Distance must be greater than zero.")
      .max(40_075, "Distance cannot exceed the Earth's circumference."),
    passengers: z
      .number({ invalid_type_error: "Passengers must be a number." })
      .int("Passengers must be a whole number.")
      .min(1, "There must be at least one passenger.")
      .max(1_000, "Passengers exceeds a sane upper limit.")
      .optional(),
  })
  .superRefine((value, ctx) => {
    if (value.mode === "carpool" && (value.passengers ?? 1) < 2) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["passengers"],
        message: "Carpooling needs at least two passengers to save anything.",
      });
    }
  });
export type SavingsRequest = z.infer<typeof savingsRequestSchema>;

/** Successful response for any savings write. Points are server-authoritative. */
export const savingsResponseSchema = z.object({
  kg_co2e_saved: z.number(),
  verified: z.boolean(),
  points_awarded: z.number(),
  badges_unlocked: z.array(z.string()),
  streak_days: z.number().optional(),
  request_id: z.string().optional(),
});
export type SavingsResponse = z.infer<typeof savingsResponseSchema>;

/** One parsed CSV row for carpool trip-history import. */
export const carpoolImportRowSchema = z.object({
  date: z.string().optional(),
  distance_km: z
    .number({ invalid_type_error: "Distance must be a number." })
    .positive("Distance must be greater than zero.")
    .max(40_075, "Distance cannot exceed the Earth's circumference."),
  passengers: z
    .number({ invalid_type_error: "Passengers must be a number." })
    .int("Passengers must be a whole number.")
    .min(2, "Carpooling needs at least two passengers.")
    .max(1_000, "Passengers exceeds a sane upper limit."),
});
export type CarpoolImportRow = z.infer<typeof carpoolImportRowSchema>;

/** Request body for `POST /api/savings/import` (bulk carpool rows). */
export const savingsImportRequestSchema = z.object({
  rows: z
    .array(carpoolImportRowSchema)
    .min(1, "Add at least one row to import.")
    .max(500, "Too many rows; split the file into smaller imports."),
});
export type SavingsImportRequest = z.infer<typeof savingsImportRequestSchema>;

/** Aggregated outcome of a bulk import. */
export const savingsImportResponseSchema = z.object({
  total_kg_co2e_saved: z.number(),
  rows_imported: z.number(),
  points_awarded: z.number(),
  badges_unlocked: z.array(z.string()),
  request_id: z.string().optional(),
});
export type SavingsImportResponse = z.infer<typeof savingsImportResponseSchema>;

/** Fields a vision model extracts from a transit ticket (best-effort). */
export const ticketExtractionSchema = z.object({
  origin: z.string().nullable().optional(),
  destination: z.string().nullable().optional(),
  mode: savingsModeSchema.nullable().optional(),
  date: z.string().nullable().optional(),
  fare: z.number().nullable().optional(),
});
export type TicketExtraction = z.infer<typeof ticketExtractionSchema>;

/** Response for `POST /api/savings/ticket` — savings plus what was read. */
export const ticketResponseSchema = savingsResponseSchema.extend({
  extraction: ticketExtractionSchema.optional(),
});
export type TicketResponse = z.infer<typeof ticketResponseSchema>;

/* ---------------------------------------------------------------------------
 * Social: anonymous regional leaderboard and profile.
 * ------------------------------------------------------------------------- */

/** Leaderboard scope — your geo-region cohort or everyone. */
export const LEADERBOARD_SCOPES = ["region", "global"] as const;
export const leaderboardScopeSchema = z.enum(LEADERBOARD_SCOPES);
export type LeaderboardScope = z.infer<typeof leaderboardScopeSchema>;

/** A single ranked, anonymised competitor. */
export const leaderboardEntrySchema = z.object({
  anon_handle: z.string(),
  /** Optional server-provided decorative emoji; derived client-side if absent. */
  emoji: z.string().optional(),
  score: z.number(),
  rank: z.number(),
  /** True for the signed-in user's own row, when the backend marks it. */
  is_me: z.boolean().optional(),
});
export type LeaderboardEntry = z.infer<typeof leaderboardEntrySchema>;

/** Response for `GET /api/leaderboard?scope=region|global`. */
export const leaderboardResponseSchema = z.object({
  scope: leaderboardScopeSchema,
  region: z.string().nullable().optional(),
  entries: z.array(leaderboardEntrySchema),
  my_rank: z.number().nullable().optional(),
  percentile: z.number().nullable().optional(),
  /** Rule-based level-up tips; the backend always sends an array (may be empty). */
  tips: z.array(z.string()),
});
export type LeaderboardResponse = z.infer<typeof leaderboardResponseSchema>;

/** Response for `GET /api/profile` — the signed-in user's public-safe state. */
export const profileResponseSchema = z.object({
  anon_handle: z.string(),
  emoji: z.string().optional(),
  region: z.string().nullable().optional(),
  points: z.number(),
  streak_days: z.number(),
  badges: z.array(z.string()),
  total_kg_co2e_saved: z.number(),
  my_rank: z.number().nullable().optional(),
  percentile: z.number().nullable().optional(),
});
export type ProfileResponse = z.infer<typeof profileResponseSchema>;

/** Human-readable labels for savings modes (web + mobile parity). */
export const SAVINGS_MODE_LABELS: Record<SavingsMode, string> = {
  carpool: "Carpool",
  bus: "Bus",
  rail: "Rail",
};

/** Human-readable labels for savings sources. */
export const SAVINGS_SOURCE_LABELS: Record<SavingsSource, string> = {
  manual: "Manual entry",
  import: "CSV import",
  ticket: "Verified ticket",
};

/**
 * Display labels for known badge ids emitted by the gamification service.
 * Unknown ids fall back to a title-cased rendering in the UI.
 */
export const BADGE_LABELS: Record<string, string> = {
  bronze: "Bronze",
  silver: "Silver",
  gold: "Gold",
  week_warrior: "Week Warrior",
  fortnight_hero: "Fortnight Hero",
  verified_rider: "Verified Rider",
};
