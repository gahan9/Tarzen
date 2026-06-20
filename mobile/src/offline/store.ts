// SPDX-License-Identifier: MIT
/**
 * Minimal async key-value store abstraction.
 *
 * The offline queue depends on this interface, not on AsyncStorage directly, so
 * its logic can be unit-tested with an in-memory store and zero native mocks.
 * The production wiring (`AsyncStorageStore`) is a thin adapter loaded only by
 * the app, never by the pure-logic tests.
 */

export interface KeyValueStore {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

/** In-memory store for tests and ephemeral fallback. */
export class InMemoryStore implements KeyValueStore {
  private readonly map = new Map<string, string>();

  async getItem(key: string): Promise<string | null> {
    return this.map.has(key) ? (this.map.get(key) as string) : null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.map.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.map.delete(key);
  }
}
