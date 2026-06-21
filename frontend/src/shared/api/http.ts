// SPDX-License-Identifier: MIT
/**
 * Shared request helper for the typed API clients.
 *
 * Mirrors the contract discipline established in `client.ts` (trace header,
 * bearer auth, zod-validated responses, typed {@link ApiError}) but factored so
 * the savings/social clients don't duplicate it. Supports JSON and multipart
 * bodies. Mock mode is handled by each caller before reaching here.
 */

import { type ZodType } from "zod";
import { errorEnvelopeSchema } from "@carbon/shared-types";

import { newTraceId, TRACE_HEADER } from "../telemetry/trace";
import { ApiError } from "./errors";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === "true";

export type TokenProvider = () => Promise<string | null>;

export interface ApiRequest<T> {
  path: string;
  method: "GET" | "POST";
  /** zod schema the success response is validated against. */
  schema: ZodType<T>;
  /** JSON body (ignored when `formData` is set). */
  body?: unknown;
  /** Multipart body for file uploads. */
  formData?: FormData;
  query?: Record<string, string | undefined>;
  signal?: AbortSignal;
  getToken?: TokenProvider;
}

function buildUrl(path: string, query?: Record<string, string | undefined>): string {
  const url = `${API_BASE_URL}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

/**
 * Performs a typed request, returning the validated success payload.
 *
 * @throws {ApiError} on validation failure, network error, or a non-2xx
 *   response. Re-throws `AbortError` so callers can ignore cancellations.
 */
export async function apiRequest<T>(request: ApiRequest<T>): Promise<T> {
  const traceId = newTraceId();

  const headers: Record<string, string> = {
    Accept: "application/json",
    [TRACE_HEADER]: traceId,
  };
  if (!request.formData) {
    headers["Content-Type"] = "application/json";
  }

  const token = request.getToken ? await request.getToken() : null;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(request.path, request.query), {
      method: request.method,
      headers,
      body: request.formData ?? (request.body ? JSON.stringify(request.body) : undefined),
      signal: request.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") {
      throw cause;
    }
    throw new ApiError({
      code: "network_error",
      message: "Could not reach the server. Check your connection and try again.",
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

  const parsed = request.schema.safeParse(payload);
  if (!parsed.success) {
    throw new ApiError({
      code: "contract_error",
      message: "The server returned data in an unexpected format.",
      requestId: null,
      traceId,
    });
  }
  return parsed.data;
}
