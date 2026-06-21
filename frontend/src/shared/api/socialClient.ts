// SPDX-License-Identifier: MIT
/**
 * Typed client for the social read endpoints:
 *  - `GET /api/leaderboard?scope=region|global`
 *  - `GET /api/profile`
 *
 * Responses are validated against the shared zod contract. A
 * `VITE_USE_MOCK_API` path mirrors each endpoint for backend-free development.
 */

import {
  leaderboardResponseSchema,
  profileResponseSchema,
  type LeaderboardResponse,
  type LeaderboardScope,
  type ProfileResponse,
} from "@carbon/shared-types";

import { apiRequest, USE_MOCK, type TokenProvider } from "./http";
import { mockLeaderboard, mockProfile } from "./socialMock";

export interface QueryOptions {
  signal?: AbortSignal;
  getToken?: TokenProvider;
}

/** Fetches the leaderboard for a scope (region cohort or global). */
export async function getLeaderboard(
  scope: LeaderboardScope,
  options: QueryOptions = {},
): Promise<LeaderboardResponse> {
  if (USE_MOCK) return mockLeaderboard(scope);

  return apiRequest({
    path: "/api/leaderboard",
    method: "GET",
    schema: leaderboardResponseSchema,
    query: { scope },
    signal: options.signal,
    getToken: options.getToken,
  });
}

/** Fetches the signed-in user's anonymised profile. */
export async function getProfile(
  options: QueryOptions = {},
): Promise<ProfileResponse> {
  if (USE_MOCK) return mockProfile();

  return apiRequest({
    path: "/api/profile",
    method: "GET",
    schema: profileResponseSchema,
    signal: options.signal,
    getToken: options.getToken,
  });
}
