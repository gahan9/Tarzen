// SPDX-License-Identifier: MIT
/**
 * Firebase initialisation.
 *
 * Config is read entirely from Vite env vars (`import.meta.env.VITE_*`) so no
 * project values are hard-coded. These web-config values are not secrets, but
 * keeping them in env makes the build portable across environments.
 *
 * If config is absent (e.g. local UI dev without a Firebase project), auth is
 * treated as unconfigured and the app runs in an anonymous, sign-in-disabled
 * mode rather than crashing.
 */

import { initializeApp, type FirebaseApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  type Auth,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId,
);

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (isFirebaseConfigured) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
}

export const googleProvider = new GoogleAuthProvider();

/** Returns the initialised Auth instance, or null when Firebase is unconfigured. */
export function getAuthOrNull(): Auth | null {
  return auth;
}
