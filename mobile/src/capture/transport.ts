// SPDX-License-Identifier: MIT
/**
 * Opt-in, consented transport capture (Google Fit + Maps-assisted).
 *
 * This service is the single gate through which any location/fitness-derived
 * trip data may flow. It refuses to capture unless (1) the user has granted
 * in-app consent and (2) the OS-level permission request succeeds. By default
 * (no consent) capture is denied — proven by the consent-gate unit test.
 *
 * Dependency-injected (consent reader, OS permission, trip sampler) so it is
 * unit-testable without expo-location / Fit native modules.
 */

import {
  TRANSPORT_MODE_LABELS,
  type TransportMode,
} from "@carbon/shared-types";

import { ConsentDeniedError } from "./consent";

/** Reads current consent for a scope. Backed by `ConsentStore` in the app. */
export interface ConsentReader {
  has(scope: "location" | "fitness"): boolean;
}

/** OS-level permission prompt (e.g. expo-location). Returns whether granted. */
export interface LocationPermission {
  request(): Promise<boolean>;
}

/** Maps/Fit-assisted distance estimate for the most recent trip (km). */
export interface TripSampler {
  sampleDistanceKm(): Promise<number>;
}

export interface CapturedTrip {
  readonly mode: TransportMode;
  readonly distanceKm: number;
  /** Human-readable note describing how the estimate was derived. */
  readonly assist: string;
}

export interface TransportCaptureDeps {
  readonly consent: ConsentReader;
  readonly permission: LocationPermission;
  readonly sampler: TripSampler;
}

/**
 * Describes the assisted-capture strategy per mode. Exhaustive over the
 * {@link TransportMode} union: the `never` default makes adding a new mode to
 * `@carbon/shared-types` a compile-time error here until it is handled.
 */
export function assistedCaptureHint(mode: TransportMode): string {
  const label = TRANSPORT_MODE_LABELS[mode];
  switch (mode) {
    case "car":
      return `${label}: Maps trip distance, speed profile confirms driving.`;
    case "bus":
      return `${label}: Maps transit match along a known route.`;
    case "rail":
      return `${label}: Maps transit match; Fit shows low step cadence.`;
    case "flight":
      return `${label}: large great-circle jump between airports.`;
    default: {
      const exhaustive: never = mode;
      return exhaustive;
    }
  }
}

export class TransportCaptureService {
  constructor(private readonly deps: TransportCaptureDeps) {}

  /** Whether capture is permitted right now (in-app consent granted). */
  canCaptureTransport(): boolean {
    return this.deps.consent.has("location");
  }

  /**
   * Captures an assisted trip for `mode`.
   *
   * @throws {ConsentDeniedError} when location consent is absent or the OS
   *   permission prompt is denied. No location/Fit read happens in that case.
   */
  async captureTransport(mode: TransportMode): Promise<CapturedTrip> {
    if (!this.deps.consent.has("location")) {
      throw new ConsentDeniedError("location");
    }
    const granted = await this.deps.permission.request();
    if (!granted) {
      throw new ConsentDeniedError("location");
    }
    const distanceKm = await this.deps.sampler.sampleDistanceKm();
    return { mode, distanceKm, assist: assistedCaptureHint(mode) };
  }
}
