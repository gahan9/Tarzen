// SPDX-License-Identifier: MIT
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { VisuallyHidden } from "./VisuallyHidden";

describe("VisuallyHidden", () => {
  it("keeps content in the accessibility tree while hiding it visually", () => {
    render(<VisuallyHidden>Loading results</VisuallyHidden>);
    const node = screen.getByText("Loading results");
    expect(node).toBeInTheDocument();
    // Clipped off-screen rather than removed, so screen readers still announce.
    expect(node).toHaveStyle({ position: "absolute", overflow: "hidden" });
  });
});
