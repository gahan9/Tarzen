// SPDX-License-Identifier: MIT
/**
 * Unit tests for the consent gate — the Phase 9 Done-gate: "no location/Fit
 * data captured without explicit consent". Capture must be denied by default.
 */

import { type TransportMode } from "@carbon/shared-types";

import {
  ConsentDeniedError,
  ConsentStore,
  NO_CONSENT,
  type ConsentScope,
} from "../src/capture/consent";
import {
  assistedCaptureHint,
  TransportCaptureService,
  type ConsentReader,
  type LocationPermission,
  type TripSampler,
} from "../src/capture/transport";
import { InMemoryStore } from "../src/offline/store";

/** A consent reader whose answer we can flip in the test. */
function fakeConsent(granted: boolean): ConsentReader {
  return { has: (_scope: ConsentScope) => granted };
}

describe("TransportCaptureService consent gate", () => {
  it("denies capture by default (no consent) without touching native modules", async () => {
    const permission: LocationPermission = {
      request: jest.fn(async () => true),
    };
    const sampler: TripSampler = {
      sampleDistanceKm: jest.fn(async () => 5),
    };
    const service = new TransportCaptureService({
      consent: fakeConsent(false),
      permission,
      sampler,
    });

    expect(service.canCaptureTransport()).toBe(false);
    await expect(service.captureTransport("car")).rejects.toBeInstanceOf(
      ConsentDeniedError,
    );
    // Crucially, no permission prompt or location read was attempted.
    expect(permission.request).not.toHaveBeenCalled();
    expect(sampler.sampleDistanceKm).not.toHaveBeenCalled();
  });

  it("still denies capture when consent is granted but the OS permission is refused", async () => {
    const permission: LocationPermission = {
      request: jest.fn(async () => false),
    };
    const sampler: TripSampler = {
      sampleDistanceKm: jest.fn(async () => 5),
    };
    const service = new TransportCaptureService({
      consent: fakeConsent(true),
      permission,
      sampler,
    });

    await expect(service.captureTransport("car")).rejects.toBeInstanceOf(
      ConsentDeniedError,
    );
    expect(permission.request).toHaveBeenCalledTimes(1);
    expect(sampler.sampleDistanceKm).not.toHaveBeenCalled();
  });

  it("captures only when consent AND permission are both granted", async () => {
    const service = new TransportCaptureService({
      consent: fakeConsent(true),
      permission: { request: async () => true },
      sampler: { sampleDistanceKm: async () => 12.5 },
    });

    const trip = await service.captureTransport("rail");
    expect(trip.mode).toBe("rail");
    expect(trip.distanceKm).toBe(12.5);
    expect(trip.assist).toContain("Rail");
  });
});

describe("ConsentStore", () => {
  it("defaults to no consent and persists grants/revokes durably", async () => {
    const store = new InMemoryStore();
    const consent = new ConsentStore(store);
    await consent.load();

    expect(consent.current()).toEqual(NO_CONSENT);
    expect(consent.has("location")).toBe(false);

    await consent.grant("location");
    expect(consent.has("location")).toBe(true);

    // A fresh store instance over the same backing storage restores the choice.
    const reloaded = new ConsentStore(store);
    await reloaded.load();
    expect(reloaded.has("location")).toBe(true);
    expect(reloaded.has("fitness")).toBe(false);

    await reloaded.revoke("location");
    expect(reloaded.has("location")).toBe(false);
  });
});

describe("assistedCaptureHint", () => {
  it("returns a hint for every transport mode", () => {
    const modes: TransportMode[] = ["car", "bus", "rail", "flight"];
    for (const mode of modes) {
      expect(assistedCaptureHint(mode).length).toBeGreaterThan(0);
    }
  });
});
