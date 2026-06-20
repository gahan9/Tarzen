// SPDX-License-Identifier: MIT
/**
 * API client for the footprint endpoint (mirrors `frontend/src/shared/api`).
 *
 * Responsibilities:
 *  - attach `Authorization: Bearer <id-token>` when the user is signed in;
 *  - attach an `X-Trace-Id` for cross-service correlation;
 *  - validate request and response against the shared zod schemas (one contract
 *    for web and mobile);
 *  - translate any failure into a typed {@link ApiError} carrying a user-safe
 *    message (from the error envelope when available).
 *
 * A mockable mode (`env.useMockApi`) lets the whole app run without a backend.
 */

import {
  errorEnvelopeSchema,
  footprintRequestSchema,
  footprintResponseSchema,
  type FootprintRequest,
  type FootprintResponse,
} from "@carbon/shared-types";

import { env } from "../config/env";
import { newTraceId, TRACE_HEADER } from "../telemetry/trace";
import { ApiError } from "./errors";
import { mockFootprint } from "./mock";

export type TokenProvider = () => Promise<string | null>;

export interface SubmitFootprintOptions {
  signal?: AbortSignal;
  getToken?: TokenProvider;
  /** Override the trace id (e.g. reuse a queued log's stable client id). */
  traceId?: string;
}

/**
 * Submits a footprint request and returns the validated success response.
 *
 * @throws {ApiError} on validation failure, network error, or a non-2xx
 *   response. Never rejects with an unstructured error (except an AbortError
 *   when the caller cancels via `signal`).
 */
export async function submitFootprint(
  request: FootprintRequest,
  options: SubmitFootprintOptions = {},
): Promise<FootprintResponse> {
  const traceId = options.traceId ?? newTraceId();

  // Client-side validation (trust nothing; fail fast with a clear message).
  const parsedRequest = footprintRequestSchema.safeParse(request);
  if (!parsedRequest.success) {
    throw new ApiError({
      code: "validation_error",
      message: parsedRequest.error.issues[0]?.message ?? "Invalid input.",
      requestId: null,
      traceId,
    });
  }

  if (env.useMockApi) {
    return mockFootprint(parsedRequest.data);
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    [TRACE_HEADER]: traceId,
  };

  const token = options.getToken ? await options.getToken() : null;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${env.apiBaseUrl}/api/footprint`, {
      method: "POST",
      headers,
      body: JSON.stringify(parsedRequest.data),
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") {
      throw cause;
    }
    throw new ApiError({
      code: "network_error",
      message:
        "Could not reach the server. Your entry is saved and will sync when you're back online.",
      requestId: null,
      traceId,
    });
  }

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const envelope = errorEnvelopeSchema.safeParse(payload);
    if (envelope.success) {
      throw new ApiError({
        code: envelope.data.error.code,
        message: envelope.data.error.message,
        requestId: envelope.data.error.request_id,
        traceId,
      });
    }
    throw new ApiError({
      code: "unexpected_error",
      message: `Request failed (HTTP ${response.status}).`,
      requestId: null,
      traceId,
    });
  }

  const parsedResponse = footprintResponseSchema.safeParse(payload);
  if (!parsedResponse.success) {
    throw new ApiError({
      code: "contract_error",
      message: "The server returned data in an unexpected format.",
      requestId: null,
      traceId,
    });
  }

  return parsedResponse.data;
}
