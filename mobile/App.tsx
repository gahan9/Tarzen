// SPDX-License-Identifier: MIT
/**
 * ROADMAP STUB (plan Phase 9 — React Native + Expo mobile app).
 *
 * This is an intentional scaffold, not a finished app. It demonstrates that
 * the mobile target consumes the same `@carbon/shared-types` contract as the
 * web app (single source of truth for request/response shapes and validation).
 * See README.md for the planned capabilities (offline-first logging, FCM
 * nudges, opt-in Google Fit + Maps transport capture).
 */

import { StatusBar } from "expo-status-bar";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import {
  TRANSPORT_MODES,
  TRANSPORT_MODE_LABELS,
  type TransportMode,
} from "@carbon/shared-types";

const ROADMAP: readonly string[] = [
  "Offline-first log queue with sync on reconnect",
  "Firebase Auth (shared ID-token contract with web)",
  "FCM nudges for streaks and weekly challenges",
  "Opt-in Google Fit + Maps transport capture (consented)",
];

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.badge}>Roadmap stub — Phase 9</Text>
        <Text style={styles.title}>Carbon Footprint</Text>
        <Text style={styles.subtitle}>
          Mobile companion (Expo + React Native). Reuses the shared API contract.
        </Text>

        <Text style={styles.sectionTitle}>Transport modes (from shared-types)</Text>
        {TRANSPORT_MODES.map((mode: TransportMode) => (
          <Text key={mode} style={styles.item}>
            • {TRANSPORT_MODE_LABELS[mode]}
          </Text>
        ))}

        <Text style={styles.sectionTitle}>Planned capabilities</Text>
        {ROADMAP.map((entry) => (
          <Text key={entry} style={styles.item}>
            • {entry}
          </Text>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f6b46" },
  content: { padding: 24, paddingTop: 72, gap: 6 },
  badge: { color: "#cdebdd", fontWeight: "600", marginBottom: 8 },
  title: { color: "#ffffff", fontSize: 32, fontWeight: "700" },
  subtitle: { color: "#e6f3ec", fontSize: 16, marginBottom: 16 },
  sectionTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "600",
    marginTop: 20,
    marginBottom: 4,
  },
  item: { color: "#e6f3ec", fontSize: 15 },
});
