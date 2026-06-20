// SPDX-License-Identifier: MIT
import { describe, expect, it } from "vitest";
import { type FootprintRequest } from "@carbon/shared-types";

import { mockFootprint } from "./mock";

function request(overrides: Partial<FootprintRequest> = {}): FootprintRequest {
  return { domain: "transport", mode: "car", distance_km: 100, ...overrides };
}

describe("mockFootprint", () => {
  it("computes kg CO2e from the per-km factor", () => {
    const result = mockFootprint(request({ mode: "car", distance_km: 100 }));
    // 100 km * 0.171 = 17.1
    expect(result.kg_co2e).toBe(17.1);
    expect(result.breakdown).toHaveLength(1);
    expect(result.breakdown[0]?.label).toBe("car travel");
  });

  it("splits the footprint across passengers", () => {
    const solo = mockFootprint(request({ distance_km: 100, passengers: 1 }));
    const shared = mockFootprint(request({ distance_km: 100, passengers: 2 }));
    expect(shared.kg_co2e).toBeCloseTo(solo.kg_co2e / 2, 5);
  });

  it("flags long-haul flights as needing more context", () => {
    const result = mockFootprint(request({ mode: "flight", distance_km: 5000 }));
    expect(result.insight.needs_context).toBe(true);
    expect(result.insight.actions).toContain("Tell us the cabin class");
  });

  it("does not request context for short trips", () => {
    const result = mockFootprint(request({ mode: "rail", distance_km: 200 }));
    expect(result.insight.needs_context).toBe(false);
    expect(result.insight.llm_used).toBe(false);
  });

  it("attaches a request id", () => {
    expect(mockFootprint(request()).request_id).toBeTruthy();
  });
});
