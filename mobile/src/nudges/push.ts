// SPDX-License-Identifier: MIT
/**
 * Push-nudge scaffolding (FCM via Expo notifications).
 *
 * Delivers streak reminders and weekly-challenge nudges. Fully gated: every
 * entry point is a safe no-op unless `EXPO_PUBLIC_ENABLE_PUSH=true` AND an EAS
 * project id is configured (required to mint an Expo push token, which is the
 * client handle FCM/APNs deliver through). This keeps a fresh checkout runnable
 * offline and avoids requesting notification permission the user never opted in
 * to.
 */

import * as Notifications from "expo-notifications";

import { env } from "../config/env";

/** True only when push is both enabled and minimally configured. */
export function isPushConfigured(): boolean {
  return env.enablePush && Boolean(env.easProjectId);
}

/** Installs the foreground notification handler. No-op unless configured. */
export function configureNudgeHandler(): void {
  if (!isPushConfigured()) return;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: false,
      shouldSetBadge: false,
    }),
  });
}

/**
 * Requests permission and returns the Expo push token to register with the
 * backend, or `null` when push is unconfigured or the user declined.
 */
export async function registerForPushNudges(): Promise<string | null> {
  if (!isPushConfigured()) return null;

  const settings = await Notifications.getPermissionsAsync();
  let granted = settings.granted;
  if (!granted) {
    const request = await Notifications.requestPermissionsAsync();
    granted = request.granted;
  }
  if (!granted) return null;

  const token = await Notifications.getExpoPushTokenAsync({
    projectId: env.easProjectId,
  });
  return token.data;
}

/** Subscribes to tapped/received nudges. Returns a no-op unsubscribe when off. */
export function subscribeToNudges(
  onReceive: (notification: Notifications.Notification) => void,
): () => void {
  if (!isPushConfigured()) return () => undefined;
  const subscription = Notifications.addNotificationReceivedListener(onReceive);
  return () => subscription.remove();
}
