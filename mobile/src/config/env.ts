// SPDX-License-Identifier: MIT
/**
 * Centralised, typed access to Expo public configuration.
 *
 * Expo inlines `EXPO_PUBLIC_*` variables into `process.env` at build time. We
 * read them once here so the rest of the app depends on a single typed object
 * rather than scattering `process.env` reads. No secrets live here — only
 * client-safe configuration (see `.env.example`).
 */

export interface FirebaseConfig {
  readonly apiKey?: string;
  readonly authDomain?: string;
  readonly projectId?: string;
  readonly storageBucket?: string;
  readonly messagingSenderId?: string;
  readonly appId?: string;
}

export interface AppEnv {
  readonly apiBaseUrl: string;
  readonly useMockApi: boolean;
  readonly firebase: FirebaseConfig;
  readonly enablePush: boolean;
  readonly easProjectId?: string;
}

function flag(value: string | undefined): boolean {
  return value === "true";
}

const firebase: FirebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID,
};

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "";

export const env: AppEnv = {
  apiBaseUrl,
  // Default to the mock when explicitly requested OR when no backend URL is
  // configured, so a fresh checkout runs fully offline out of the box.
  useMockApi: flag(process.env.EXPO_PUBLIC_USE_MOCK_API) || apiBaseUrl === "",
  firebase,
  enablePush: flag(process.env.EXPO_PUBLIC_ENABLE_PUSH),
  easProjectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID,
};

/** True when enough Firebase config is present to initialise auth. */
export const isFirebaseConfigured = Boolean(
  firebase.apiKey && firebase.authDomain && firebase.projectId,
);
