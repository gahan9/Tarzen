// SPDX-License-Identifier: MIT
/**
 * App-wide wiring for the offline-first log queue.
 *
 * Owns the singleton {@link OfflineLogQueue} (backed by AsyncStorage), tracks
 * connectivity via NetInfo, flushes the queue on reconnect, and exposes the
 * state the screens need (online flag, pending logs, computed results). The
 * queue's submit callback calls the real API with the signed-in user's ID token
 * and the log's stable `clientId` as the trace id.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  type FootprintRequest,
  type FootprintResponse,
} from "@carbon/shared-types";

import { submitFootprint } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { newTraceId } from "../telemetry/trace";
import { AsyncStorageStore } from "./asyncStorageStore";
import { netInfoSource } from "./netinfoSource";
import { OfflineLogQueue, type QueuedLog } from "./queue";
import { startReconnectSync } from "./reconnect";

export interface LoggedResult {
  readonly clientId: string;
  readonly request: FootprintRequest;
  readonly response: FootprintResponse;
  readonly at: string;
}

export interface QueueContextValue {
  readonly online: boolean;
  readonly pending: readonly QueuedLog[];
  readonly results: readonly LoggedResult[];
  /** Queues a log, then attempts to sync. Returns the result if it synced now. */
  submitLog: (request: FootprintRequest) => Promise<FootprintResponse | null>;
  syncNow: () => Promise<void>;
}

const QueueContext = createContext<QueueContextValue | null>(null);

export function QueueProvider({ children }: { children: ReactNode }) {
  const { getIdToken } = useAuth();
  const [online, setOnline] = useState(true);
  const [pending, setPending] = useState<readonly QueuedLog[]>([]);
  const [results, setResults] = useState<readonly LoggedResult[]>([]);

  // Keep the latest token getter in a ref so the stable submit callback always
  // reads a fresh token without re-creating the queue.
  const getTokenRef = useRef(getIdToken);
  getTokenRef.current = getIdToken;

  // One-shot resolvers so `submitLog` can await the result of the sync it kicks
  // off (resolved by the queue's submit callback on success).
  const resolversRef = useRef(
    new Map<string, (result: FootprintResponse | null) => void>(),
  );

  const queueRef = useRef<OfflineLogQueue | null>(null);
  if (queueRef.current === null) {
    const store = new AsyncStorageStore();
    queueRef.current = new OfflineLogQueue(store, async (log) => {
      const response = await submitFootprint(log.request, {
        getToken: () => getTokenRef.current(),
        traceId: log.clientId,
      });
      setResults((prev) => [
        {
          clientId: log.clientId,
          request: log.request,
          response,
          at: new Date().toISOString(),
        },
        ...prev,
      ]);
      const resolve = resolversRef.current.get(log.clientId);
      if (resolve) {
        resolve(response);
        resolversRef.current.delete(log.clientId);
      }
    });
  }
  const queue = queueRef.current;

  const refreshPending = useCallback(() => {
    setPending(queue.pending());
  }, [queue]);

  const syncNow = useCallback(async () => {
    await queue.sync();
    refreshPending();
  }, [queue, refreshPending]);

  useEffect(() => {
    let active = true;
    void queue.load().then(() => {
      if (active) refreshPending();
    });
    const stopReconnect = startReconnectSync(queue, netInfoSource);
    const stopOnline = netInfoSource.subscribe((state) => {
      setOnline(state.isConnected === true);
    });
    // Reflect pending changes shortly after a reconnect sync completes.
    const unsubscribeAfterSync = netInfoSource.subscribe(() => {
      setTimeout(refreshPending, 0);
    });
    return () => {
      active = false;
      stopReconnect();
      stopOnline();
      unsubscribeAfterSync();
    };
  }, [queue, refreshPending]);

  const submitLog = useCallback(
    async (request: FootprintRequest): Promise<FootprintResponse | null> => {
      const clientId = newTraceId();
      const settled = new Promise<FootprintResponse | null>((resolve) => {
        resolversRef.current.set(clientId, resolve);
      });
      await queue.enqueue(request, clientId);
      refreshPending();
      await queue.sync();
      refreshPending();
      // If it did not sync now (offline / failure) it stays queued; resolve null
      // so the UI can show the "saved, will sync later" state.
      const stillPending = queue
        .pending()
        .some((log) => log.clientId === clientId);
      if (stillPending) {
        const resolve = resolversRef.current.get(clientId);
        if (resolve) {
          resolve(null);
          resolversRef.current.delete(clientId);
        }
      }
      return settled;
    },
    [queue, refreshPending],
  );

  const value = useMemo<QueueContextValue>(
    () => ({ online, pending, results, submitLog, syncNow }),
    [online, pending, results, submitLog, syncNow],
  );

  return <QueueContext.Provider value={value}>{children}</QueueContext.Provider>;
}

export function useLogQueue(): QueueContextValue {
  const ctx = useContext(QueueContext);
  if (!ctx) {
    throw new Error("useLogQueue must be used within a <QueueProvider>.");
  }
  return ctx;
}
