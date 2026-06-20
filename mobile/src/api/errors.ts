// SPDX-License-Identifier: MIT
/** Normalised API error surfaced to the UI. Always has a user-safe message. */
export class ApiError extends Error {
  readonly code: string;
  readonly requestId: string | null;
  readonly traceId: string;

  constructor(params: {
    code: string;
    message: string;
    requestId: string | null;
    traceId: string;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.code = params.code;
    this.requestId = params.requestId;
    this.traceId = params.traceId;
  }
}

/**
 * True when an error indicates the request never reached the server (offline,
 * DNS failure, timeout). The offline queue uses this to decide whether to keep
 * an entry for a later retry versus surfacing a hard failure.
 */
export function isNetworkError(error: unknown): boolean {
  return error instanceof ApiError && error.code === "network_error";
}
