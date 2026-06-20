// SPDX-License-Identifier: MIT
/**
 * Firebase initialisation for React Native.
 *
 * Mirrors the web app's contract (the ID token obtained here is attached as
 * `Authorization: Bearer <token>` on API calls) but uses `initializeAuth` with
 * AsyncStorage-backed React Native persistence so the session survives restarts.
 *
 * Config is read entirely from Expo env (`EXPO_PUBLIC_*`, see `config/env.ts`).
 * These web config values are not secrets. When config is absent, auth is left
 * unconfigured and the app runs anonymously rather than crashing.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { getApps, initializeApp, type FirebaseApp } from "firebase/app";
import {
  initializeAuth,
  GoogleAuthProvider,
  type Auth,
  type Persistence,
} from "firebase/auth";
// `getReactNativePersistence` exists at runtime in firebase v10 but is omitted
// from the public `firebase/auth` type surface, so we bind it through a typed
// view rather than a direct named import.
import * as firebaseAuth from "firebase/auth";

import { env, isFirebaseConfigured } from "../config/env";

const getReactNativePersistence = (
  firebaseAuth as unknown as {
    getReactNativePersistence: (storage: unknown) => Persistence;
  }
).getReactNativePersistence;

let auth: Auth | null = null;

if (isFirebaseConfigured) {
  const apps = getApps();
  const app: FirebaseApp = apps[0] ?? initializeApp(env.firebase);
  auth = initializeAuth(app, {
    persistence: getReactNativePersistence(AsyncStorage),
  });
}

export const googleProvider = new GoogleAuthProvider();

/** Returns the initialised Auth instance, or null when Firebase is unconfigured. */
export function getAuthOrNull(): Auth | null {
  return auth;
}

export { isFirebaseConfigured };
