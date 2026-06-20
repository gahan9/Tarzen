// SPDX-License-Identifier: MIT
/**
 * Footprint page: composes the form with the result/insight area and owns the
 * explicit idle / loading / error / success rendering. The result region
 * receives focus on change for keyboard and screen-reader users.
 */

import { useFootprint } from "./useFootprint";
import { FootprintForm } from "./FootprintForm";
import { InsightCard } from "../insights/InsightCard";
import { useFocusOnChange } from "../../shared/a11y/useFocusOnChange";

export function FootprintPage() {
  const { state, submit } = useFootprint();
  const focusKey =
    state.status === "success" || state.status === "error"
      ? state.status
      : null;
  const resultRef = useFocusOnChange<HTMLElement>(focusKey);

  return (
    <div className="footprint-layout">
      <FootprintForm onSubmit={submit} pending={state.status === "loading"} />

      <div aria-live="polite" className="footprint-result">
        {state.status === "idle" ? (
          <p className="result-empty">
            Enter a trip to see its estimated carbon footprint and tips to
            reduce it.
          </p>
        ) : null}

        {state.status === "loading" ? (
          <p className="result-loading" role="status">
            Calculating your footprint…
          </p>
        ) : null}

        {state.status === "error" ? (
          <section
            ref={resultRef}
            tabIndex={-1}
            role="alert"
            className="result-error"
            aria-labelledby="error-heading"
          >
            <h2 id="error-heading">We couldn&apos;t calculate that</h2>
            <p>{state.message}</p>
            {state.requestId ? (
              <p className="result-error-id">Reference: {state.requestId}</p>
            ) : null}
          </section>
        ) : null}

        {state.status === "success" ? (
          <InsightCard ref={resultRef} result={state.data} />
        ) : null}
      </div>
    </div>
  );
}
