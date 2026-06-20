// SPDX-License-Identifier: MIT
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { useFocusOnChange } from "./useFocusOnChange";

function Probe({ token }: { token: number }) {
  const ref = useFocusOnChange<HTMLDivElement>(token);
  return (
    <div ref={ref} tabIndex={-1} data-testid="target">
      Outcome {token}
    </div>
  );
}

describe("useFocusOnChange", () => {
  it("moves focus to the element when the key becomes truthy", () => {
    render(<Probe token={1} />);
    expect(screen.getByTestId("target")).toHaveFocus();
  });

  it("does not focus when the key is falsy", () => {
    render(<Probe token={0} />);
    expect(screen.getByTestId("target")).not.toHaveFocus();
  });

  it("re-focuses when the key changes to a new truthy value", () => {
    const { rerender } = render(<Probe token={1} />);
    const target = screen.getByTestId("target");
    target.blur();
    expect(target).not.toHaveFocus();
    rerender(<Probe token={2} />);
    expect(screen.getByTestId("target")).toHaveFocus();
  });
});
