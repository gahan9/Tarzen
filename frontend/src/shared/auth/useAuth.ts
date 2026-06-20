// SPDX-License-Identifier: MIT
import { useContext } from "react";

import { AuthContext, type AuthContextValue } from "./context";

/** Access the auth context; throws if used outside <AuthProvider>. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an <AuthProvider>.");
  }
  return ctx;
}
