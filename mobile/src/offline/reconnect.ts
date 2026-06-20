// SPDX-License-Identifier: MIT
/**
 * Reconnect-driven sync wiring.
 *
 * Bridges a connectivity source (NetInfo in production, a fake in tests) to the
 * offline queue: whenever the device transitions from offline to online, the
 * queue is flushed. Defined over a tiny {@link ConnectivitySource} interface so
 * the reconnect behaviour can be unit-tested without NetInfo.
 */

import { type OfflineLogQueue } from "./queue";

export interface ConnectivityState {
  /** `null` = unknown (before the first probe). */
  readonly isConnected: boolean | null;
}

export type ConnectivityListener = (state: ConnectivityState) => void;
export type Unsubscribe = () => void;

export interface ConnectivitySource {
  subscribe(listener: ConnectivityListener): Unsubscribe;
}

/**
 * Starts syncing `queue` on every offline->online transition.
 *
 * Treats the first observed "connected" state as a transition too, so a log
 * queued before the listener attached still flushes once connectivity is known.
 *
 * @returns an unsubscribe function to stop listening.
 */
export function startReconnectSync(
  queue: OfflineLogQueue,
  source: ConnectivitySource,
): Unsubscribe {
  let wasConnected: boolean | null = null;
  return source.subscribe((state) => {
    const connected = state.isConnected === true;
    const becameConnected = connected && wasConnected !== true;
    wasConnected = connected;
    if (becameConnected && queue.pendingCount() > 0) {
      void queue.sync();
    }
  });
}
