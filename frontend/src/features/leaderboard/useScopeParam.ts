// SPDX-License-Identifier: MIT
/**
 * Keeps the leaderboard scope in the URL (`?scope=region|global`) so a board is
 * shareable and survives reloads. Falls back to `region` for missing/invalid
 * values.
 */

import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  leaderboardScopeSchema,
  type LeaderboardScope,
} from "@carbon/shared-types";

export function useScopeParam(): [LeaderboardScope, (next: LeaderboardScope) => void] {
  const [params, setParams] = useSearchParams();
  const parsed = leaderboardScopeSchema.safeParse(params.get("scope"));
  const scope: LeaderboardScope = parsed.success ? parsed.data : "region";

  const setScope = useCallback(
    (next: LeaderboardScope) => {
      setParams({ scope: next }, { replace: true });
    },
    [setParams],
  );

  return [scope, setScope];
}
