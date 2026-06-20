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
