// SPDX-License-Identifier: MIT
/**
 * Local mock of `POST /api/footprint` for development and offline runs, gated by
 * `EXPO_PUBLIC_USE_MOCK_API` (see `env.ts`). It mirrors the backend contract
 * (rule-based numbers are illustrative only) so the app can be exercised end to
 * end without a live backend. Mirrors the web app's mock for parity.
 */

import {
  type FootprintRequest,
  type FootprintResponse,
  type TransportMode,
} from "@carbon/shared-types";

import { newTraceId } from "../telemetry/trace";

/** Illustrative per-km factors (kg CO2e per passenger-km). Not authoritative. */
const MOCK_FACTORS: Record<TransportMode, number> = {
  car: 0.171,
  bus: 0.103,
  rail: 0.041,
  flight: 0.255,
};

export function mockFootprint(request: FootprintRequest): FootprintResponse {
  const passengers = request.passengers ?? 1;
  const factor = MOCK_FACTORS[request.mode];
  const total = (request.distance_km * factor) / passengers;
  const rounded = Math.round(total * 100) / 100;
  const needsContext = request.mode === "flight" && request.distance_km > 3000;

  return {
    kg_co2e: rounded,
    breakdown: [{ label: `${request.mode} travel`, kg_co2e: rounded }],
    insight: {
      message: needsContext
        ? "That's a long-haul trip. A few details would help me tailor advice."
        : "Nice — every tracked trip is a step toward understanding your impact.",
      benchmark: `About ${(rounded / 0.4).toFixed(1)} kg CO2e ~= ${(
        rounded / 0.12
      ).toFixed(0)} smartphone charges.`,
      actions: needsContext
        ? ["Tell us the cabin class", "Was this round-trip?"]
        : [
            "Try combining errands into one trip",
            "Consider rail for trips under 700 km",
          ],
      needs_context: needsContext,
      llm_used: false,
    },
    request_id: newTraceId(),
  };
}
