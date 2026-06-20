// SPDX-License-Identifier: MIT
import { type ReactNode } from "react";

const style: React.CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
  border: 0,
};

/**
 * Renders content for assistive technology only (visually hidden, still in the
 * accessibility tree). Use for labels/announcements that would be visually
 * redundant but help screen-reader users.
 */
export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span style={style}>{children}</span>;
}
