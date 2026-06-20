// SPDX-License-Identifier: MIT
import { describe, expect, it, vi, afterEach } from "vitest";

import { newTraceId, TRACE_HEADER } from "./trace";

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

describe("newTraceId", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("exposes the canonical trace header name", () => {
    expect(TRACE_HEADER).toBe("X-Trace-Id");
  });

  it("returns a v4 UUID via crypto.randomUUID when available", () => {
    const id = newTraceId();
    expect(id).toMatch(UUID_V4);
  });

  it("returns unique ids across calls", () => {
    expect(newTraceId()).not.toBe(newTraceId());
  });

  it("falls back to a manual v4 generator when crypto is absent", () => {
    vi.stubGlobal("crypto", undefined);
    const id = newTraceId();
    expect(id).toMatch(UUID_V4);
  });
});
