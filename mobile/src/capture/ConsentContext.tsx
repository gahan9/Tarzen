// SPDX-License-Identifier: MIT
/**
 * App-wide consent + transport-capture wiring.
 *
 * Owns the persisted {@link ConsentStore} and a {@link TransportCaptureService}
 * built from the expo-location adapters. Exposes consent state and a guarded
 * `captureTransport` to the UI. Capture is denied until the user grants consent
 * here (first gate) and the OS permission prompt succeeds (second gate).
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
import { type TransportMode } from "@carbon/shared-types";

import { AsyncStorageStore } from "../offline/asyncStorageStore";
import {
  ConsentStore,
  NO_CONSENT,
  type ConsentScope,
  type ConsentState,
} from "./consent";
import { expoLocationPermission, expoLocationSampler } from "./expoLocation";
import { TransportCaptureService, type CapturedTrip } from "./transport";

export interface ConsentContextValue {
  readonly consent: ConsentState;
  readonly canCaptureTransport: boolean;
  grant: (scope: ConsentScope) => Promise<void>;
  revoke: (scope: ConsentScope) => Promise<void>;
  captureTransport: (mode: TransportMode) => Promise<CapturedTrip>;
}

const ConsentContext = createContext<ConsentContextValue | null>(null);

export function ConsentProvider({ children }: { children: ReactNode }) {
  const [consent, setConsent] = useState<ConsentState>(NO_CONSENT);

  const storeRef = useRef<ConsentStore | null>(null);
  if (storeRef.current === null) {
    storeRef.current = new ConsentStore(new AsyncStorageStore());
  }
  const consentStore = storeRef.current;

  const serviceRef = useRef<TransportCaptureService | null>(null);
  if (serviceRef.current === null) {
    serviceRef.current = new TransportCaptureService({
      consent: consentStore,
      permission: expoLocationPermission,
      sampler: expoLocationSampler,
    });
  }
  const service = serviceRef.current;

  useEffect(() => {
    void consentStore.load().then(() => setConsent(consentStore.current()));
  }, [consentStore]);

  const grant = useCallback(
    async (scope: ConsentScope) => {
      await consentStore.grant(scope);
      setConsent(consentStore.current());
    },
    [consentStore],
  );

  const revoke = useCallback(
    async (scope: ConsentScope) => {
      await consentStore.revoke(scope);
      setConsent(consentStore.current());
    },
    [consentStore],
  );

  const captureTransport = useCallback(
    (mode: TransportMode) => service.captureTransport(mode),
    [service],
  );

  const value = useMemo<ConsentContextValue>(
    () => ({
      consent,
      canCaptureTransport: consent.location,
      grant,
      revoke,
      captureTransport,
    }),
    [consent, grant, revoke, captureTransport],
  );

  return (
    <ConsentContext.Provider value={value}>{children}</ConsentContext.Provider>
  );
}

export function useConsent(): ConsentContextValue {
  const ctx = useContext(ConsentContext);
  if (!ctx) {
    throw new Error("useConsent must be used within a <ConsentProvider>.");
  }
  return ctx;
}
