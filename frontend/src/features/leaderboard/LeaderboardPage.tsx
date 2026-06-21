// SPDX-License-Identifier: MIT
/**
 * Anonymous leaderboard. Toggle between your regional cohort and the global
 * board; each row shows a rank medal, the emoji-decorated anonymous handle, and
 * the score. Your own row is highlighted, and rule-based level-up tips help you
 * climb. Only anonymised handles and scores are ever shown.
 */

import { useCallback, useEffect } from "react";
import {
  LEADERBOARD_SCOPES,
  type LeaderboardEntry,
  type LeaderboardScope,
} from "@carbon/shared-types";

import { getLeaderboard } from "../../shared/api/socialClient";
import { useAsyncFn } from "../../shared/hooks/useAsyncFn";
import { useAuth } from "../../shared/auth/useAuth";
import { Emoji } from "../../shared/ui/Emoji";
import { emojiForHandle, emojiForRank } from "../../shared/ui/emojiMap";
import { useScopeParam } from "./useScopeParam";

const SCOPE_LABELS: Record<LeaderboardScope, string> = {
  region: "My region",
  global: "Global",
};

const numberFormat = new Intl.NumberFormat();

function EntryRow({ entry }: { entry: LeaderboardEntry }) {
  return (
    <li className={entry.is_me ? "lb-row lb-row--me" : "lb-row"}>
      <span className="lb-rank">
        <Emoji name={emojiForRank(entry.rank)} label={`Rank ${entry.rank}`} />
        <span className="lb-rank-num">{entry.rank}</span>
      </span>
      <span className="lb-handle">
        <Emoji name={emojiForHandle(entry.anon_handle, entry.emoji)} />{" "}
        {entry.anon_handle}
        {entry.is_me ? <span className="lb-you"> (you)</span> : null}
      </span>
      <span className="lb-score">
        {numberFormat.format(entry.score)}
        <span className="lb-score-unit"> pts</span>
      </span>
    </li>
  );
}

export function LeaderboardPage() {
  const { getIdToken } = useAuth();
  const [scope, setScope] = useScopeParam();

  const { state, run } = useAsyncFn(
    useCallback(
      (signal: AbortSignal, next: LeaderboardScope) =>
        getLeaderboard(next, { signal, getToken: getIdToken }),
      [getIdToken],
    ),
  );

  useEffect(() => {
    void run(scope);
  }, [run, scope]);

  return (
    <section aria-labelledby="lb-heading" className="lb-page">
      <h1 id="lb-heading">
        <Emoji name="leaderboard" /> Leaderboard
      </h1>

      <div className="tabs" role="tablist" aria-label="Leaderboard scope">
        {LEADERBOARD_SCOPES.map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={scope === item}
            className={scope === item ? "tab tab--active" : "tab"}
            onClick={() => setScope(item)}
          >
            <Emoji name={item === "region" ? "region" : "globe"} />{" "}
            {SCOPE_LABELS[item]}
          </button>
        ))}
      </div>

      <div aria-live="polite">
        {state.status === "loading" ? (
          <p className="result-loading" role="status">
            Loading the leaderboard…
          </p>
        ) : null}

        {state.status === "error" ? (
          <p role="alert" className="field-error">
            {state.message}
          </p>
        ) : null}

        {state.status === "success" ? (
          <>
            {state.data.my_rank != null ? (
              <p className="lb-mystanding">
                <Emoji name="trophy" /> You&apos;re rank{" "}
                <strong>#{state.data.my_rank}</strong>
                {state.data.percentile != null ? (
                  <> — top {100 - state.data.percentile}% of this board.</>
                ) : null}
              </p>
            ) : null}

            <ol className="lb-list">
              {state.data.entries.map((entry) => (
                <EntryRow key={`${entry.rank}-${entry.anon_handle}`} entry={entry} />
              ))}
            </ol>

            {state.data.tips.length > 0 ? (
              <section className="lb-tips" aria-labelledby="lb-tips-heading">
                <h2 id="lb-tips-heading">
                  <Emoji name="tip" /> Level up
                </h2>
                <ul>
                  {state.data.tips.map((tip, index) => (
                    <li key={`tip-${index}`}>
                      <Emoji name="sprout" /> {tip}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
