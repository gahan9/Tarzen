// SPDX-License-Identifier: MIT
import { useEffect, useRef } from "react";

/**
 * Returns a ref that moves keyboard focus to the element whenever `key`
 * changes to a truthy value. Used to move focus to the result/error region
 * after submission so screen-reader and keyboard users are taken to the
 * outcome rather than left on the form.
 */
export function useFocusOnChange<T extends HTMLElement>(
  key: unknown,
): React.RefObject<T> {
  const ref = useRef<T>(null);
  useEffect(() => {
    if (key) {
      ref.current?.focus();
    }
  }, [key]);
  return ref;
}
