// SPDX-License-Identifier: MIT
import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiError } from "../api/errors";
import { useAsyncFn } from "./useAsyncFn";

describe("useAsyncFn", () => {
  it("starts idle and transitions to success with data", async () => {
    const { result } = renderHook(() =>
      useAsyncFn(async (_signal: AbortSignal, value: number) => value * 2),
    );
    expect(result.current.state).toEqual({ status: "idle" });

    await act(async () => {
      await result.current.run(21);
    });

    expect(result.current.state).toEqual({ status: "success", data: 42 });
  });

  it("aborts the previous in-flight call (latest call wins)", async () => {
    const signals: AbortSignal[] = [];
    const { result } = renderHook(() =>
      useAsyncFn(async (signal: AbortSignal) => {
        signals.push(signal);
        // Never resolves: keeps both calls in-flight so we can assert that the
        // second invocation aborts the first without late, post-act setState.
        return new Promise<number>(() => {});
      }),
    );

    await act(async () => {
      void result.current.run();
      void result.current.run();
      await Promise.resolve();
    });

    expect(signals[0]!.aborted).toBe(true);
    expect(signals[1]!.aborted).toBe(false);
  });

  it("maps an ApiError to an error state with its message and request id", async () => {
    const { result } = renderHook(() =>
      useAsyncFn(async () => {
        throw new ApiError({
          code: "rate_limited",
          message: "Too many requests.",
          requestId: "req-7",
          traceId: "trace-7",
        });
      }),
    );

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.state).toEqual({
      status: "error",
      message: "Too many requests.",
      requestId: "req-7",
    });
  });

  it("maps an unknown error to a generic message with no request id", async () => {
    const { result } = renderHook(() =>
      useAsyncFn(async () => {
        throw new Error("kaboom");
      }),
    );

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.state).toEqual({
      status: "error",
      message: "Something went wrong. Please try again.",
      requestId: null,
    });
  });

  it("swallows an AbortError without entering an error state", async () => {
    const { result } = renderHook(() =>
      useAsyncFn(async () => {
        throw new DOMException("aborted", "AbortError");
      }),
    );

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.state).toEqual({ status: "loading" });
  });

  it("reset returns the state to idle", async () => {
    const { result } = renderHook(() =>
      useAsyncFn(async () => "done"),
    );

    await act(async () => {
      await result.current.run();
    });
    expect(result.current.state.status).toBe("success");

    act(() => {
      result.current.reset();
    });
    expect(result.current.state).toEqual({ status: "idle" });
  });
});
