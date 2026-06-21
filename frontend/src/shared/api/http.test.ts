// SPDX-License-Identifier: MIT
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { ApiError } from "./errors";
import { apiRequest, IDEMPOTENCY_HEADER, newIdempotencyKey } from "./http";

const schema = z.object({ value: z.number() });

function jsonResponse(body: unknown, init: { ok?: boolean; status?: number } = {}) {
  return {
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => body,
  } as Response;
}

describe("apiRequest", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns the validated success payload", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: 42 }));

    const data = await apiRequest({ path: "/x", method: "GET", schema });

    expect(data).toEqual({ value: 42 });
  });

  it("sends the trace header, JSON content-type, and bearer token", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: 1 }));

    await apiRequest({
      path: "/x",
      method: "POST",
      schema,
      body: { a: 1 },
      getToken: async () => "tok",
    });

    const [, init] = vi.mocked(fetch).mock.calls[0]!;
    const headers = init!.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers.Authorization).toBe("Bearer tok");
    expect(init!.body).toBe(JSON.stringify({ a: 1 }));
  });

  it("sends the Idempotency-Key header when provided", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: 1 }));

    await apiRequest({
      path: "/x",
      method: "POST",
      schema,
      body: {},
      idempotencyKey: "key-123",
    });

    const [, init] = vi.mocked(fetch).mock.calls[0]!;
    const headers = init!.headers as Record<string, string>;
    expect(headers[IDEMPOTENCY_HEADER]).toBe("key-123");
  });

  it("omits Content-Type for multipart bodies", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: 1 }));
    const formData = new FormData();
    formData.append("image", new Blob(["x"]), "x.png");

    await apiRequest({ path: "/x", method: "POST", schema, formData });

    const [, init] = vi.mocked(fetch).mock.calls[0]!;
    const headers = init!.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBeUndefined();
    expect(init!.body).toBe(formData);
  });

  it("maps a backend error envelope to an ApiError", async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse(
        { error: { code: "rate_limited", message: "Slow down.", request_id: "r-9" } },
        { ok: false, status: 429 },
      ),
    );

    await expect(
      apiRequest({ path: "/x", method: "GET", schema }),
    ).rejects.toMatchObject({
      code: "rate_limited",
      message: "Slow down.",
      requestId: "r-9",
    });
  });

  it("falls back to unexpected_error for an unrecognised error body", async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ nope: true }, { ok: false, status: 500 }),
    );

    await expect(
      apiRequest({ path: "/x", method: "GET", schema }),
    ).rejects.toMatchObject({ code: "unexpected_error", requestId: null });
  });

  it("raises contract_error when the success body fails validation", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: "not-a-number" }));

    await expect(
      apiRequest({ path: "/x", method: "GET", schema }),
    ).rejects.toMatchObject({ code: "contract_error" });
  });

  it("raises network_error when fetch rejects with a non-abort error", async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError("offline"));

    const err = await apiRequest({ path: "/x", method: "GET", schema }).catch(
      (e) => e,
    );
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("network_error");
  });

  it("rethrows an AbortError so callers can ignore cancellations", async () => {
    vi.mocked(fetch).mockRejectedValue(new DOMException("aborted", "AbortError"));

    const err = await apiRequest({ path: "/x", method: "GET", schema }).catch(
      (e) => e,
    );
    expect(err).toBeInstanceOf(DOMException);
    expect(err.name).toBe("AbortError");
  });

  it("builds a query string from defined params only", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ value: 1 }));

    await apiRequest({
      path: "/x",
      method: "GET",
      schema,
      query: { scope: "region", skip: undefined },
    });

    const [url] = vi.mocked(fetch).mock.calls[0]!;
    expect(url).toBe("/x?scope=region");
  });
});

describe("newIdempotencyKey", () => {
  it("mints a unique key per call", () => {
    expect(newIdempotencyKey()).not.toBe(newIdempotencyKey());
  });
});
