// SPDX-License-Identifier: MIT
/**
 * Offline-first footprint log queue.
 *
 * Day-to-day tracking must never require connectivity. Logs are appended to a
 * locally persisted FIFO queue and submitted opportunistically — immediately if
 * online, otherwise on the next reconnect (see `reconnect.ts`). Key properties:
 *
 *  - **Durable**: every mutation is persisted via an injected {@link KeyValueStore}
 *    so entries survive an app restart or crash before they sync.
 *  - **Deduplicated**: each log has a stable `clientId`; enqueuing the same id
 *    twice (double tap, replayed event) is a no-op, and ids already synced are
 *    never re-queued. The same id is reused as the request trace id so the
 *    server can dedupe idempotently too.
 *  - **Order-preserving & resilient**: `sync()` submits in FIFO order and stops
 *    at the first failure, keeping the unsent tail for the next attempt.
 *
 * The class is framework-free and dependency-injected so it is unit-testable in
 * plain Node without mocking AsyncStorage or NetInfo.
 */

import { type FootprintRequest } from "@carbon/shared-types";

import { newTraceId } from "../telemetry/trace";
import { type KeyValueStore } from "./store";

export interface QueuedLog {
  /** Stable dedupe key; also reused as the API trace id. */
  readonly clientId: string;
  readonly request: FootprintRequest;
  readonly createdAt: string;
  /** Number of failed submit attempts so far. */
  readonly attempts: number;
}

/** Submits a single queued log. Should reject on any non-success. */
export type SubmitLog = (log: QueuedLog) => Promise<void>;

export interface EnqueueResult {
  readonly log: QueuedLog;
  /** True when the id already existed and nothing new was queued. */
  readonly deduped: boolean;
}

export interface SyncResult {
  readonly synced: number;
  readonly remaining: number;
  /** The error that halted syncing, if any (e.g. still offline). */
  readonly error?: unknown;
}

interface PersistedState {
  readonly pending: QueuedLog[];
  readonly syncedIds: string[];
}

/** How many recently-synced ids to remember for dedupe (bounded memory). */
const SYNCED_ID_HISTORY = 200;

export const DEFAULT_QUEUE_KEY = "carbon.offline.footprint-queue.v1";

export class OfflineLogQueue {
  private pendingLogs: QueuedLog[] = [];
  private syncedIds: string[] = [];
  private syncing = false;

  constructor(
    private readonly store: KeyValueStore,
    private readonly submit: SubmitLog,
    private readonly storageKey: string = DEFAULT_QUEUE_KEY,
  ) {}

  /** Hydrates in-memory state from the persisted store. Call once on startup. */
  async load(): Promise<void> {
    const raw = await this.store.getItem(this.storageKey);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as Partial<PersistedState>;
      this.pendingLogs = Array.isArray(parsed.pending) ? parsed.pending : [];
      this.syncedIds = Array.isArray(parsed.syncedIds) ? parsed.syncedIds : [];
    } catch {
      // Corrupt payload: start clean rather than crash the app.
      this.pendingLogs = [];
      this.syncedIds = [];
    }
  }

  /** Snapshot of unsent logs in submit order. */
  pending(): readonly QueuedLog[] {
    return [...this.pendingLogs];
  }

  pendingCount(): number {
    return this.pendingLogs.length;
  }

  private knows(clientId: string): boolean {
    return (
      this.syncedIds.includes(clientId) ||
      this.pendingLogs.some((log) => log.clientId === clientId)
    );
  }

  /**
   * Adds a log to the queue. Deduplicates on `clientId`: a repeated id (already
   * pending or already synced) is ignored.
   */
  async enqueue(
    request: FootprintRequest,
    clientId: string = newTraceId(),
  ): Promise<EnqueueResult> {
    if (this.knows(clientId)) {
      const existing = this.pendingLogs.find((log) => log.clientId === clientId);
      return {
        log:
          existing ??
          { clientId, request, createdAt: new Date().toISOString(), attempts: 0 },
        deduped: true,
      };
    }

    const log: QueuedLog = {
      clientId,
      request,
      createdAt: new Date().toISOString(),
      attempts: 0,
    };
    this.pendingLogs.push(log);
    await this.persist();
    return { log, deduped: false };
  }

  /**
   * Attempts to submit every pending log in FIFO order. Stops at the first
   * failure (typically "still offline") and keeps the unsent tail for the next
   * reconnect. Re-entrant calls are coalesced.
   */
  async sync(): Promise<SyncResult> {
    if (this.syncing) {
      return { synced: 0, remaining: this.pendingLogs.length };
    }
    this.syncing = true;
    let synced = 0;
    try {
      while (this.pendingLogs.length > 0) {
        const next = this.pendingLogs[0] as QueuedLog;
        try {
          await this.submit(next);
        } catch (error) {
          this.pendingLogs[0] = { ...next, attempts: next.attempts + 1 };
          await this.persist();
          return { synced, remaining: this.pendingLogs.length, error };
        }
        this.pendingLogs.shift();
        this.rememberSynced(next.clientId);
        synced += 1;
        await this.persist();
      }
      return { synced, remaining: 0 };
    } finally {
      this.syncing = false;
    }
  }

  private rememberSynced(clientId: string): void {
    this.syncedIds.push(clientId);
    if (this.syncedIds.length > SYNCED_ID_HISTORY) {
      this.syncedIds = this.syncedIds.slice(-SYNCED_ID_HISTORY);
    }
  }

  private async persist(): Promise<void> {
    const state: PersistedState = {
      pending: this.pendingLogs,
      syncedIds: this.syncedIds,
    };
    await this.store.setItem(this.storageKey, JSON.stringify(state));
  }
}
