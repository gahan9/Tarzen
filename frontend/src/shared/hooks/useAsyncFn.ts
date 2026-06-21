// SPDX-License-Identifier: MIT
/**
 * Small async state machine for a single in-flight operation.
 *
 * Mirrors the explicit idle/loading/success/error pattern in `useFootprint`,
 * generalised so the savings, leaderboard, and profile features don't each
 * re-implement abort handling and {@link ApiError} translation. The latest call
 * always wins: a new invocation aborts the previous one.
 */

import { useCallback, useRef, useState } from "react";

import { ApiError } from "../api/errors";

export type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; message: string; requestId: string | null };

export function useAsyncFn<Args extends unknown[], T>(
  fn: (signal: AbortSignal, ...args: Args) => Promise<T>,
) {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(
    async (...args: Args): Promise<T | undefined> => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setState({ status: "loading" });

      try {
        const data = await fn(controller.signal, ...args);
        if (!controller.signal.aborted) {
          setState({ status: "success", data });
        }
        return data;
      } catch (cause) {
        if (cause instanceof DOMException && cause.name === "AbortError") {
          return undefined;
        }
        if (cause instanceof ApiError) {
          setState({
            status: "error",
            message: cause.message,
            requestId: cause.requestId,
          });
          return undefined;
        }
        setState({
          status: "error",
          message: "Something went wrong. Please try again.",
          requestId: null,
        });
        return undefined;
      }
    },
    [fn],
  );

  const reset = useCallback(() => setState({ status: "idle" }), []);

  return { state, run, reset };
}
