// SPDX-License-Identifier: MIT
/**
 * Unit tests for the offline-first log queue and reconnect-driven sync — the
 * Phase 9 Done-gate: "offline log syncs on reconnect" and entries are deduped.
 */

import { type FootprintRequest } from "@carbon/shared-types";

import {
  OfflineLogQueue,
  type QueuedLog,
  type SubmitLog,
} from "../src/offline/queue";
import {
  startReconnectSync,
  type ConnectivityListener,
  type ConnectivitySource,
} from "../src/offline/reconnect";
import { InMemoryStore } from "../src/offline/store";

const REQUEST: FootprintRequest = {
  domain: "transport",
  mode: "car",
  distance_km: 10,
  passengers: 1,
};

/** Resolves once `predicate` is true, flushing microtasks between checks. */
async function waitFor(predicate: () => boolean, tries = 50): Promise<void> {
  for (let i = 0; i < tries; i += 1) {
    if (predicate()) return;
    await new Promise((resolve) => setImmediate(resolve));
  }
  throw new Error("waitFor: condition never became true");
}

/** A connectivity source whose state we can drive manually in tests. */
function fakeConnectivity() {
  const listeners: ConnectivityListener[] = [];
  const source: ConnectivitySource = {
    subscribe(listener) {
      listeners.push(listener);
      return () => {
        const index = listeners.indexOf(listener);
        if (index >= 0) listeners.splice(index, 1);
      };
    },
  };
  return {
    source,
    emit(isConnected: boolean | null) {
      for (const listener of [...listeners]) listener({ isConnected });
    },
  };
}

describe("OfflineLogQueue", () => {
  it("keeps entries queued while offline, then syncs them on reconnect", async () => {
    const store = new InMemoryStore();
    let online = false;
    const submitted: string[] = [];
    const submit: SubmitLog = async (log: QueuedLog) => {
      if (!online) throw new Error("offline");
      submitted.push(log.clientId);
    };

    const queue = new OfflineLogQueue(store, submit);
    await queue.load();
    await queue.enqueue(REQUEST, "a");
    await queue.enqueue(REQUEST, "b");

    const net = fakeConnectivity();
    startReconnectSync(queue, net.source);

    // Offline event: nothing should sync.
    net.emit(false);
    await waitFor(() => true);
    expect(submitted).toEqual([]);
    expect(queue.pendingCount()).toBe(2);

    // Reconnect: the queue flushes in FIFO order.
    online = true;
    net.emit(true);
    await waitFor(() => queue.pendingCount() === 0);
    expect(submitted).toEqual(["a", "b"]);
  });

  it("deduplicates a repeated clientId in the pending queue", async () => {
    const store = new InMemoryStore();
    const submit: SubmitLog = async () => {
      throw new Error("offline");
    };
    const queue = new OfflineLogQueue(store, submit);

    const first = await queue.enqueue(REQUEST, "dup");
    const second = await queue.enqueue(REQUEST, "dup");

    expect(first.deduped).toBe(false);
    expect(second.deduped).toBe(true);
    expect(queue.pendingCount()).toBe(1);
  });

  it("never re-queues an id that has already synced", async () => {
    const store = new InMemoryStore();
    const submitted: string[] = [];
    const submit: SubmitLog = async (log) => {
      submitted.push(log.clientId);
    };
    const queue = new OfflineLogQueue(store, submit);

    await queue.enqueue(REQUEST, "x");
    await queue.sync();
    expect(queue.pendingCount()).toBe(0);

    const again = await queue.enqueue(REQUEST, "x");
    expect(again.deduped).toBe(true);
    expect(queue.pendingCount()).toBe(0);
    expect(submitted).toEqual(["x"]); // submitted exactly once
  });

  it("stops at the first failure and keeps the unsent tail, tracking attempts", async () => {
    const store = new InMemoryStore();
    let failNext = true;
    const submitted: string[] = [];
    const submit: SubmitLog = async (log) => {
      if (failNext) throw new Error("offline");
      submitted.push(log.clientId);
    };
    const queue = new OfflineLogQueue(store, submit);
    await queue.enqueue(REQUEST, "a");
    await queue.enqueue(REQUEST, "b");

    const firstAttempt = await queue.sync();
    expect(firstAttempt.synced).toBe(0);
    expect(queue.pendingCount()).toBe(2);
    expect(queue.pending()[0]?.attempts).toBe(1);

    failNext = false;
    const secondAttempt = await queue.sync();
    expect(secondAttempt.synced).toBe(2);
    expect(submitted).toEqual(["a", "b"]);
  });

  it("persists pending entries so they survive a restart", async () => {
    const store = new InMemoryStore();
    const offline: SubmitLog = async () => {
      throw new Error("offline");
    };
    const queue = new OfflineLogQueue(store, offline);
    await queue.enqueue(REQUEST, "persisted");
    expect(queue.pendingCount()).toBe(1);

    // Simulate an app restart: a brand-new queue over the same store.
    const restarted = new OfflineLogQueue(store, offline);
    await restarted.load();
    expect(restarted.pendingCount()).toBe(1);
    expect(restarted.pending()[0]?.clientId).toBe("persisted");
  });
});
