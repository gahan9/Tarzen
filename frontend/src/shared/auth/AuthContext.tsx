// SPDX-License-Identifier: MIT
/**
 * Auth context: wraps Firebase Auth and exposes the current user plus the
 * actions the UI needs. The ID token obtained here is what the API client
 * attaches as `Authorization: Bearer <token>`.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";

import { getAuthOrNull, googleProvider, isFirebaseConfigured } from "./firebase";
import { AuthContext, type AuthContextValue } from "./context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    const auth = getAuthOrNull();
    if (!auth) {
      setInitializing(false);
      return;
    }
    const unsubscribe = onAuthStateChanged(auth, (next) => {
      setUser(next);
      setInitializing(false);
    });
    return unsubscribe;
  }, []);

  const signInWithGoogle = useCallback(async () => {
    const auth = getAuthOrNull();
    if (!auth) throw new Error("Authentication is not configured.");
    await signInWithPopup(auth, googleProvider);
  }, []);

  const signInWithEmail = useCallback(
    async (email: string, password: string) => {
      const auth = getAuthOrNull();
      if (!auth) throw new Error("Authentication is not configured.");
      await signInWithEmailAndPassword(auth, email, password);
    },
    [],
  );

  const signOut = useCallback(async () => {
    const auth = getAuthOrNull();
    if (!auth) return;
    await firebaseSignOut(auth);
  }, []);

  const getIdToken = useCallback(async () => {
    const current = getAuthOrNull()?.currentUser;
    if (!current) return null;
    return current.getIdToken();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initializing,
      configured: isFirebaseConfigured,
      signInWithGoogle,
      signInWithEmail,
      signOut,
      getIdToken,
    }),
    [user, initializing, signInWithGoogle, signInWithEmail, signOut, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
