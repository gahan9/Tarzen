// SPDX-License-Identifier: MIT
/**
 * Production {@link ConnectivitySource} backed by NetInfo.
 *
 * Thin adapter (never imported by pure-logic tests) that maps NetInfo's state
 * onto the queue's minimal connectivity interface.
 */

import NetInfo, { type NetInfoState } from "@react-native-community/netinfo";

import {
  type ConnectivityListener,
  type ConnectivitySource,
  type Unsubscribe,
} from "./reconnect";

export const netInfoSource: ConnectivitySource = {
  subscribe(listener: ConnectivityListener): Unsubscribe {
    return NetInfo.addEventListener((state: NetInfoState) => {
      listener({ isConnected: state.isConnected });
    });
  },
};
