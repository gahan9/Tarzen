// SPDX-License-Identifier: MIT
import { useCallback, useRef, useState } from "react";
import {
  type FootprintRequest,
  type FootprintResponse,
} from "@carbon/shared-types";

import { submitFootprint } from "../../shared/api/client";
import { ApiError } from "../../shared/api/errors";
import { useAuth } from "../../shared/auth/useAuth";

export type FootprintState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: FootprintResponse }
  | { status: "error"; message: string; requestId: string | null };

/** Drives a single footprint submission with explicit loading/error/success. */
export function useFootprint() {
  const { getIdToken } = useAuth();
  const [state, setState] = useState<FootprintState>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);

  const submit = useCallback(
    async (request: FootprintRequest) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setState({ status: "loading" });

      try {
        const data = await submitFootprint(request, {
          signal: controller.signal,
          getToken: getIdToken,
        });
        setState({ status: "success", data });
      } catch (cause) {
        if (cause instanceof DOMException && cause.name === "AbortError") {
          return;
        }
        if (cause instanceof ApiError) {
          setState({
            status: "error",
            message: cause.message,
            requestId: cause.requestId,
          });
          return;
        }
        setState({
          status: "error",
          message: "Something went wrong. Please try again.",
          requestId: null,
        });
      }
    },
    [getIdToken],
  );

  const reset = useCallback(() => setState({ status: "idle" }), []);

  return { state, submit, reset };
}
