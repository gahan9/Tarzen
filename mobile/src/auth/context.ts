// SPDX-License-Identifier: MIT
import { createContext } from "react";
import { type User } from "firebase/auth";

export interface AuthContextValue {
  /** Current signed-in user, or null. */
  user: User | null;
  /** True until the initial auth state has resolved. */
  initializing: boolean;
  /** Whether Firebase is configured at all (env present). */
  configured: boolean;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Fresh ID token for the current user, or null if signed out. */
  getIdToken: () => Promise<string | null>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
