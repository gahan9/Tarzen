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
