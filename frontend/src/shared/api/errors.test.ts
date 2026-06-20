// SPDX-License-Identifier: MIT
import { describe, expect, it } from "vitest";

import { ApiError } from "./errors";

describe("ApiError", () => {
  it("carries a user-safe message and correlation metadata", () => {
    const err = new ApiError({
      code: "validation_error",
      message: "Distance must be greater than zero.",
      requestId: "req-1",
      traceId: "trace-1",
    });
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("ApiError");
    expect(err.code).toBe("validation_error");
    expect(err.message).toBe("Distance must be greater than zero.");
    expect(err.requestId).toBe("req-1");
    expect(err.traceId).toBe("trace-1");
  });

  it("allows a null request id (pre-response failures)", () => {
    const err = new ApiError({
      code: "network_error",
      message: "Could not reach the server.",
      requestId: null,
      traceId: "trace-2",
    });
    expect(err.requestId).toBeNull();
  });
});
