// SPDX-License-Identifier: MIT
/**
 * Sign-in bar (React Native): a minimal email/password form that surfaces the
 * signed-in user and a sign-out action. Degrades gracefully with a clear
 * message when Firebase is not configured for local/offline development.
 *
 * Every interactive element carries an `accessibilityLabel`/`accessibilityRole`
 * for screen-reader users.
 */

import { useState } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useAuth } from "./useAuth";

export function SignInBar() {
  const { user, configured, initializing, signInWithEmail, signOut } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (initializing) {
    return (
      <View style={styles.bar} accessibilityRole="text">
        <Text style={styles.muted} accessibilityLabel="Checking sign-in status">
          Checking sign-in…
        </Text>
      </View>
    );
  }

  if (!configured) {
    return (
      <View style={styles.bar}>
        <Text style={styles.muted}>
          Sign-in is unconfigured. Requests are sent unauthenticated.
        </Text>
      </View>
    );
  }

  if (user) {
    return (
      <View style={styles.barRow}>
        <Text style={styles.signedIn} numberOfLines={1}>
          Signed in as {user.email ?? "user"}
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Sign out"
          style={styles.button}
          onPress={() => void signOut()}
        >
          <Text style={styles.buttonText}>Sign out</Text>
        </Pressable>
      </View>
    );
  }

  async function handleSignIn() {
    setError(null);
    try {
      await signInWithEmail(email, password);
    } catch {
      setError("Sign-in failed. Check your email and password.");
    }
  }

  return (
    <View style={styles.bar}>
      <TextInput
        style={styles.input}
        placeholder="Email"
        accessibilityLabel="Email address"
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        accessibilityLabel="Password"
        autoComplete="current-password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Sign in with email and password"
        style={styles.button}
        onPress={() => void handleSignIn()}
      >
        <Text style={styles.buttonText}>Sign in</Text>
      </Pressable>
      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { gap: 8, padding: 16, backgroundColor: "#f1f7f3", borderRadius: 12 },
  barRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    backgroundColor: "#f1f7f3",
    borderRadius: 12,
  },
  muted: { color: "#4a5b52" },
  signedIn: { color: "#0f6b46", fontWeight: "600", flexShrink: 1 },
  input: {
    borderWidth: 1,
    borderColor: "#c5d6cc",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
  },
  button: {
    backgroundColor: "#0f6b46",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: { color: "#ffffff", fontWeight: "600" },
  error: { color: "#b00020" },
});
