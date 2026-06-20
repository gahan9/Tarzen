// SPDX-License-Identifier: MIT
/**
 * Insight card: renders the footprint result — total kg CO2e, the per-line
 * breakdown, the empathetic insight message, a relatable benchmark, and a
 * short list of achievable actions. When `needs_context` is set, it surfaces
 * the follow-up prompts instead of presenting the result as final.
 */

import { forwardRef } from "react";
import { type FootprintResponse } from "@carbon/shared-types";

interface InsightCardProps {
  result: FootprintResponse;
  onAddContext?: () => void;
}

const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2,
});

export const InsightCard = forwardRef<HTMLElement, InsightCardProps>(
  function InsightCard({ result, onAddContext }, ref) {
    const { kg_co2e, breakdown, insight } = result;

    return (
      <section
        ref={ref}
        tabIndex={-1}
        aria-labelledby="insight-heading"
        className="insight-card"
      >
        <h2 id="insight-heading">Your estimated footprint</h2>

        <p className="insight-total">
          <span className="insight-total-value">
            {numberFormat.format(kg_co2e)}
          </span>{" "}
          <span className="insight-total-unit">kg CO2e</span>
        </p>

        {breakdown.length > 0 ? (
          <>
            <h3>Breakdown</h3>
            <ul className="insight-breakdown">
              {breakdown.map((item, index) => (
                <li key={`${item.label}-${index}`}>
                  <span>{item.label}</span>
                  <span>{numberFormat.format(item.kg_co2e)} kg</span>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        <p className="insight-message">{insight.message}</p>
        <p className="insight-benchmark">
          <strong>For perspective:</strong> {insight.benchmark}
        </p>

        {insight.needs_context ? (
          <div className="insight-context" role="group" aria-label="More detail needed">
            <p>To sharpen this estimate, could you tell us:</p>
            <ul>
              {insight.actions.map((prompt, index) => (
                <li key={`prompt-${index}`}>{prompt}</li>
              ))}
            </ul>
            {onAddContext ? (
              <button type="button" onClick={onAddContext}>
                Add more detail
              </button>
            ) : null}
          </div>
        ) : insight.actions.length > 0 ? (
          <>
            <h3>Small steps that help</h3>
            <ul className="insight-actions">
              {insight.actions.map((action, index) => (
                <li key={`action-${index}`}>{action}</li>
              ))}
            </ul>
          </>
        ) : null}

        <p className="insight-source">
          {insight.llm_used
            ? "Phrasing assisted by AI; the numbers are computed deterministically."
            : "Generated from deterministic emission factors."}
        </p>
      </section>
    );
  },
);
