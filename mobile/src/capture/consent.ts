// SPDX-License-Identifier: MIT
/**
 * Consent state for opt-in, privacy-sensitive capture (location / fitness).
 *
 * Privacy invariant: **everything is opt-out by default.** No location or Google
 * Fit data may be read until the user has explicitly granted the relevant
 * consent here AND the OS permission has been granted. Consent is revocable and
 * persisted via an injected {@link KeyValueStore} so the choice survives
 * restarts. This module holds no secrets and performs no capture itself.
 */

import { type KeyValueStore } from "../offline/store";

export type ConsentScope = "location" | "fitness";

export interface ConsentState {
  readonly location: boolean;
  readonly fitness: boolean;
}

/** The safe default: nothing consented. */
export const NO_CONSENT: ConsentState = Object.freeze({
  location: false,
  fitness: false,
});

export const CONSENT_STORAGE_KEY = "carbon.consent.v1";

/** Raised when capture is attempted without the required consent/permission. */
export class ConsentDeniedError extends Error {
  readonly scope: ConsentScope;

  constructor(scope: ConsentScope) {
    super(`Consent not granted for "${scope}" capture.`);
    this.name = "ConsentDeniedError";
    this.scope = scope;
  }
}

/** Durable, revocable consent store. Defaults to {@link NO_CONSENT}. */
export class ConsentStore {
  private state: ConsentState = NO_CONSENT;

  constructor(
    private readonly store: KeyValueStore,
    private readonly storageKey: string = CONSENT_STORAGE_KEY,
  ) {}

  async load(): Promise<void> {
    const raw = await this.store.getItem(this.storageKey);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as Partial<ConsentState>;
      this.state = {
        location: parsed.location === true,
        fitness: parsed.fitness === true,
      };
    } catch {
      this.state = NO_CONSENT;
    }
  }

  current(): ConsentState {
    return this.state;
  }

  has(scope: ConsentScope): boolean {
    return this.state[scope];
  }

  async grant(scope: ConsentScope): Promise<void> {
    this.state = { ...this.state, [scope]: true };
    await this.persist();
  }

  async revoke(scope: ConsentScope): Promise<void> {
    this.state = { ...this.state, [scope]: false };
    await this.persist();
  }

  private async persist(): Promise<void> {
    await this.store.setItem(this.storageKey, JSON.stringify(this.state));
  }
}
