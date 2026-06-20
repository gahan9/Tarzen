// SPDX-License-Identifier: MIT
/**
 * Sign-in bar: Google sign-in plus a minimal email/password form. Surfaces the
 * signed-in user and a sign-out action. Degrades gracefully (with a clear
 * message) when Firebase is not configured for local UI development.
 */

import { useId, useState, type FormEvent } from "react";

import { useAuth } from "./useAuth";

export function SignInBar() {
  const { user, configured, initializing, signInWithGoogle, signInWithEmail, signOut } =
    useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const emailId = useId();
  const passwordId = useId();
  const errorId = useId();

  if (initializing) {
    return (
      <div className="signin-bar" role="status">
        Checking sign-in…
      </div>
    );
  }

  if (!configured) {
    return (
      <div className="signin-bar signin-bar--muted">
        Sign-in is unconfigured (set <code>VITE_FIREBASE_*</code>). Requests are
        sent unauthenticated.
      </div>
    );
  }

  if (user) {
    return (
      <div className="signin-bar">
        <span>Signed in as {user.email ?? user.displayName ?? "user"}</span>
        <button type="button" onClick={() => void signOut()}>
          Sign out
        </button>
      </div>
    );
  }

  async function handleEmailSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await signInWithEmail(email, password);
    } catch {
      setError("Sign-in failed. Check your email and password.");
    }
  }

  async function handleGoogle() {
    setError(null);
    try {
      await signInWithGoogle();
    } catch {
      setError("Google sign-in was cancelled or failed.");
    }
  }

  return (
    <div className="signin-bar">
      <button type="button" onClick={() => void handleGoogle()}>
        Sign in with Google
      </button>

      <form onSubmit={handleEmailSignIn} className="signin-email">
        <div className="field">
          <label htmlFor={emailId}>Email</label>
          <input
            id={emailId}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-describedby={error ? errorId : undefined}
          />
        </div>
        <div className="field">
          <label htmlFor={passwordId}>Password</label>
          <input
            id={passwordId}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby={error ? errorId : undefined}
          />
        </div>
        <button type="submit">Sign in</button>
      </form>

      {error ? (
        <p id={errorId} role="alert" className="field-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}
