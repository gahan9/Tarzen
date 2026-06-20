// SPDX-License-Identifier: MIT
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";

import { FootprintForm } from "./FootprintForm";

describe("FootprintForm", () => {
  it("submits a validated transport request", async () => {
    const onSubmit = vi.fn();
    render(<FootprintForm onSubmit={onSubmit} pending={false} />);

    await userEvent.type(screen.getByLabelText(/distance/i), "120");
    await userEvent.click(screen.getByRole("button", { name: /calculate/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      domain: "transport",
      mode: "car",
      distance_km: 120,
    });
  });

  it("includes passengers when provided", async () => {
    const onSubmit = vi.fn();
    render(<FootprintForm onSubmit={onSubmit} pending={false} />);

    await userEvent.type(screen.getByLabelText(/distance/i), "120");
    await userEvent.type(screen.getByLabelText(/passengers/i), "3");
    await userEvent.click(screen.getByRole("button", { name: /calculate/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      domain: "transport",
      mode: "car",
      distance_km: 120,
      passengers: 3,
    });
  });

  it("rejects invalid input with an announced error and no submit", async () => {
    const onSubmit = vi.fn();
    render(<FootprintForm onSubmit={onSubmit} pending={false} />);

    await userEvent.type(screen.getByLabelText(/distance/i), "0");
    await userEvent.click(screen.getByRole("button", { name: /calculate/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/greater than zero/i);
  });

  it.each([
    ["bus", /spread emissions across many riders/i],
    ["rail", /lowest-carbon motorised option/i],
    ["flight", /long flights dominate/i],
  ])("updates the helper hint when the mode changes to %s", async (mode, copy) => {
    render(<FootprintForm onSubmit={vi.fn()} pending={false} />);
    await userEvent.selectOptions(screen.getByLabelText(/mode of transport/i), mode);
    expect(screen.getByText(copy)).toBeInTheDocument();
  });

  it("disables the submit button while a request is pending", () => {
    render(<FootprintForm onSubmit={vi.fn()} pending />);
    expect(screen.getByRole("button", { name: /calculating/i })).toBeDisabled();
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<FootprintForm onSubmit={vi.fn()} pending={false} />);
    // color-contrast relies on canvas, which jsdom does not implement.
    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results).toHaveNoViolations();
  });
});
