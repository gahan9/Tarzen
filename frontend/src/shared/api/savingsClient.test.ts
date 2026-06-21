// SPDX-License-Identifier: MIT
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./errors";
import * as http from "./http";
import { importSavings, submitSavings, submitTicket } from "./savingsClient";

describe("savingsClient", () => {
  beforeEach(() => {
    vi.spyOn(http, "apiRequest").mockResolvedValue({} as never);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("POSTs a validated manual saving as JSON with an idempotency key", async () => {
    await submitSavings({
      source: "manual",
      mode: "carpool",
      distance_km: 30,
      passengers: 3,
    });

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.path).toBe("/api/savings");
    expect(call.method).toBe("POST");
    expect(call.body).toEqual({
      source: "manual",
      mode: "carpool",
      distance_km: 30,
      passengers: 3,
    });
    expect(call.formData).toBeUndefined();
    expect(call.idempotencyKey).toEqual(expect.any(String));
  });

  it("rejects invalid input before any network call", async () => {
    await expect(
      submitSavings({
        source: "manual",
        mode: "carpool",
        distance_km: -5,
        passengers: 3,
      }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(http.apiRequest).not.toHaveBeenCalled();
  });

  it("POSTs an import batch to the import endpoint", async () => {
    await importSavings([{ date: "2026-06-01", distance_km: 10, passengers: 2 }]);

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.path).toBe("/api/savings/import");
    expect(call.method).toBe("POST");
    expect(call.body).toEqual({
      rows: [{ date: "2026-06-01", distance_km: 10, passengers: 2 }],
    });
    expect(call.idempotencyKey).toEqual(expect.any(String));
  });

  it("uploads a ticket as multipart form data (not JSON)", async () => {
    const file = new File([new Uint8Array([1, 2, 3])], "ticket.png", {
      type: "image/png",
    });

    await submitTicket(file);

    const call = vi.mocked(http.apiRequest).mock.calls[0]![0];
    expect(call.path).toBe("/api/savings/ticket");
    expect(call.method).toBe("POST");
    expect(call.body).toBeUndefined();
    expect(call.formData).toBeInstanceOf(FormData);
    expect(call.formData!.get("image")).toBeInstanceOf(File);
    expect(call.idempotencyKey).toEqual(expect.any(String));
  });
});
