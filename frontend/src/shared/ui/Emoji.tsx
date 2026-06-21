// SPDX-License-Identifier: MIT
/**
 * Accessible emoji renderer.
 *
 * Decorative emoji must never be read by a screen reader on their own — they
 * are visual anchors beside real text. This component renders the glyph inside
 * an `aria-hidden` span. When `label` is provided it is exposed to assistive
 * tech via a visually-hidden span so the emoji always has an adjacent text
 * equivalent (satisfying the plan's a11y requirement).
 */

import { type EmojiKey, EMOJI } from "./emojiMap";
import { VisuallyHidden } from "../a11y/VisuallyHidden";

interface EmojiProps {
  /** A semantic key from the typed map, or a raw glyph string. */
  name: EmojiKey | string;
  /** Accessible text equivalent; omit only when adjacent visible text exists. */
  label?: string;
  className?: string;
}

function resolveGlyph(name: string): string {
  return (EMOJI as Record<string, string>)[name] ?? name;
}

export function Emoji({ name, label, className }: EmojiProps) {
  return (
    <>
      <span aria-hidden="true" className={className}>
        {resolveGlyph(name)}
      </span>
      {label ? <VisuallyHidden>{label}</VisuallyHidden> : null}
    </>
  );
}
