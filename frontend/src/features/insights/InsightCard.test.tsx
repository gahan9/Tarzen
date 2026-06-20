// SPDX-License-Identifier: MIT
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { type FootprintResponse } from "@carbon/shared-types";

import { InsightCard } from "./InsightCard";

function response(overrides: Partial<FootprintResponse> = {}): FootprintResponse {
  return {
    kg_co2e: 17.1,
    breakdown: [{ label: "car travel", kg_co2e: 17.1 }],
    insight: {
      message: "Nice — every tracked trip helps.",
      benchmark: "About 42 smartphone charges.",
      actions: ["Combine errands into one trip"],
      needs_context: false,
      llm_used: false,
    },
    request_id: "req-1",
    ...overrides,
  };
}

describe("InsightCard", () => {
  it("renders the total, breakdown, and actions", () => {
    render(<InsightCard result={response()} />);
    expect(
      screen.getByRole("heading", { name: /your estimated footprint/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("17.1")).toBeInTheDocument();
    expect(screen.getByText("car travel")).toBeInTheDocument();
    expect(screen.getByText("Combine errands into one trip")).toBeInTheDocument();
    expect(screen.getByText(/deterministic emission factors/i)).toBeInTheDocument();
  });

  it("notes AI assistance when the LLM was used for phrasing", () => {
    render(
      <InsightCard
        result={response({
          insight: { ...response().insight, llm_used: true },
        })}
      />,
    );
    expect(screen.getByText(/phrasing assisted by ai/i)).toBeInTheDocument();
  });

  it("shows follow-up prompts and an action button when context is needed", async () => {
    const onAddContext = vi.fn();
    render(
      <InsightCard
        result={response({
          insight: {
            ...response().insight,
            needs_context: true,
            actions: ["Tell us the cabin class"],
          },
        })}
        onAddContext={onAddContext}
      />,
    );
    expect(screen.getByText("Tell us the cabin class")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /add more detail/i }));
    expect(onAddContext).toHaveBeenCalledOnce();
  });

  it("hides the breakdown section when there are no line items", () => {
    render(<InsightCard result={response({ breakdown: [] })} />);
    expect(screen.queryByRole("heading", { name: /breakdown/i })).toBeNull();
  });

  it("omits the action button when no onAddContext handler is supplied", () => {
    render(
      <InsightCard
        result={response({
          insight: { ...response().insight, needs_context: true },
        })}
      />,
    );
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders neither prompts nor actions when none apply", () => {
    render(
      <InsightCard
        result={response({
          insight: { ...response().insight, actions: [], needs_context: false },
        })}
      />,
    );
    expect(screen.queryByRole("heading", { name: /small steps/i })).toBeNull();
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<InsightCard result={response()} />);
    // color-contrast relies on canvas, which jsdom does not implement.
    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results).toHaveNoViolations();
  });
});
