// SPDX-License-Identifier: MIT
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as http from "./http";
import { getLeaderboard, getProfile } from "./socialClient";

describe("socialClient", () => {
  beforeEach(() => {
    vi.spyOn(http, "apiRequest").mockResolvedValue({} as never);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("GETs the leaderboard with the scope query param", async () => {
    await getLeaderboard("region");

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.path).toBe("/api/leaderboard");
    expect(call.method).toBe("GET");
    expect(call.query).toEqual({ scope: "region" });
  });

  it("GETs the profile endpoint", async () => {
    await getProfile();

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.path).toBe("/api/profile");
    expect(call.method).toBe("GET");
  });

  it("forwards the abort signal and token provider", async () => {
    const controller = new AbortController();
    const getToken = async () => "tok";

    await getLeaderboard("global", { signal: controller.signal, getToken });

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.signal).toBe(controller.signal);
    expect(call.getToken).toBe(getToken);
  });
});
