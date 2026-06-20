// SPDX-License-Identifier: MIT
/**
 * Production {@link KeyValueStore} backed by AsyncStorage.
 *
 * Kept in its own file (never imported by the pure-logic tests) so the queue
 * logic stays free of native dependencies.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";

import { type KeyValueStore } from "./store";

export class AsyncStorageStore implements KeyValueStore {
  getItem(key: string): Promise<string | null> {
    return AsyncStorage.getItem(key);
  }

  setItem(key: string, value: string): Promise<void> {
    return AsyncStorage.setItem(key, value);
  }

  removeItem(key: string): Promise<void> {
    return AsyncStorage.removeItem(key);
  }
}
