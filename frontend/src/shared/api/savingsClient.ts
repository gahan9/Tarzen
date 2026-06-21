// SPDX-License-Identifier: MIT
/**
 * Typed client for the carbon-savings endpoints:
 *  - `POST /api/savings` (manual / single carpool entry)
 *  - `POST /api/savings/import` (bulk carpool rows from a CSV)
 *  - `POST /api/savings/ticket` (multipart image → verified savings)
 *
 * Each call validates input against the shared zod contract before the network
 * round-trip and the response on the way back. A `VITE_USE_MOCK_API` path
 * mirrors each endpoint for backend-free UI development.
 */

import {
  savingsImportRequestSchema,
  savingsImportResponseSchema,
  savingsRequestSchema,
  savingsResponseSchema,
  ticketResponseSchema,
  type CarpoolImportRow,
  type SavingsImportResponse,
  type SavingsRequest,
  type SavingsResponse,
  type TicketResponse,
} from "@carbon/shared-types";

import { newTraceId } from "../telemetry/trace";
import { ApiError } from "./errors";
import { apiRequest, USE_MOCK, type TokenProvider } from "./http";
import { mockImport, mockSavings, mockTicket } from "./socialMock";

export interface MutationOptions {
  signal?: AbortSignal;
  getToken?: TokenProvider;
}

function validationError(message: string): ApiError {
  return new ApiError({
    code: "validation_error",
    message,
    requestId: null,
    traceId: newTraceId(),
  });
}

/** Submits a single manual/carpool saving. */
export async function submitSavings(
  request: SavingsRequest,
  options: MutationOptions = {},
): Promise<SavingsResponse> {
  const parsed = savingsRequestSchema.safeParse(request);
  if (!parsed.success) {
    throw validationError(parsed.error.issues[0]?.message ?? "Invalid input.");
  }
  if (USE_MOCK) return mockSavings(parsed.data);

  return apiRequest({
    path: "/api/savings",
    method: "POST",
    schema: savingsResponseSchema,
    body: parsed.data,
    signal: options.signal,
    getToken: options.getToken,
  });
}

/** Imports a batch of parsed carpool rows. */
export async function importSavings(
  rows: CarpoolImportRow[],
  options: MutationOptions = {},
): Promise<SavingsImportResponse> {
  const parsed = savingsImportRequestSchema.safeParse({ rows });
  if (!parsed.success) {
    throw validationError(parsed.error.issues[0]?.message ?? "Invalid rows.");
  }
  if (USE_MOCK) return mockImport(parsed.data.rows);

  return apiRequest({
    path: "/api/savings/import",
    method: "POST",
    schema: savingsImportResponseSchema,
    body: parsed.data,
    signal: options.signal,
    getToken: options.getToken,
  });
}

/** Uploads a ticket image for vision extraction + a verified saving. */
export async function submitTicket(
  file: File,
  options: MutationOptions = {},
): Promise<TicketResponse> {
  if (USE_MOCK) return mockTicket();

  const formData = new FormData();
  formData.append("image", file, file.name);

  return apiRequest({
    path: "/api/savings/ticket",
    method: "POST",
    schema: ticketResponseSchema,
    formData,
    signal: options.signal,
    getToken: options.getToken,
  });
}
