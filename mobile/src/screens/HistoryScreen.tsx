// SPDX-License-Identifier: MIT
/**
 * History & insights screen: shows synced results (newest first) and any
 * entries still queued for sync. A manual "Sync now" action complements the
 * automatic reconnect sync. Interactive and informational elements expose
 * screen-reader labels/roles.
 */

import {
  ScrollView,
  StyleSheet,
  Text,
  Pressable,
  View,
} from "react-native";
import { TRANSPORT_MODE_LABELS } from "@carbon/shared-types";

import { useLogQueue } from "../offline/QueueContext";

export function HistoryScreen() {
  const { results, pending, online, syncNow } = useLogQueue();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <Text style={styles.title} accessibilityRole="header">
          Your activity
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Sync queued entries now"
          accessibilityState={{ disabled: pending.length === 0 }}
          disabled={pending.length === 0}
          style={[styles.syncButton, pending.length === 0 && styles.syncDisabled]}
          onPress={() => void syncNow()}
        >
          <Text style={styles.syncText}>Sync now</Text>
        </Pressable>
      </View>

      <Text style={styles.section} accessibilityRole="header">
        Pending ({pending.length}){online ? "" : " · offline"}
      </Text>
      {pending.length === 0 ? (
        <Text style={styles.muted}>Nothing waiting to sync.</Text>
      ) : (
        pending.map((log) => (
          <View key={log.clientId} style={styles.row} accessibilityRole="text">
            <Text style={styles.rowTitle}>
              {TRANSPORT_MODE_LABELS[log.request.mode]} · {log.request.distance_km} km
            </Text>
            <Text style={styles.muted}>
              Queued {new Date(log.createdAt).toLocaleTimeString()}
              {log.attempts > 0 ? ` · ${log.attempts} retr${log.attempts === 1 ? "y" : "ies"}` : ""}
            </Text>
          </View>
        ))
      )}

      <Text style={styles.section} accessibilityRole="header">
        Logged ({results.length})
      </Text>
      {results.length === 0 ? (
        <Text style={styles.muted}>No trips logged yet. Add one on the Log tab.</Text>
      ) : (
        results.map((entry) => (
          <View key={entry.clientId} style={styles.card} accessibilityRole="summary">
            <Text style={styles.rowTitle}>
              {TRANSPORT_MODE_LABELS[entry.request.mode]} ·{" "}
              {entry.response.kg_co2e.toFixed(2)} kg CO2e
            </Text>
            <Text style={styles.muted}>{entry.response.insight.benchmark}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#ffffff" },
  content: { padding: 16, gap: 8 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontSize: 22, fontWeight: "700", color: "#22302a" },
  section: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0f6b46",
    marginTop: 12,
  },
  row: {
    borderBottomWidth: 1,
    borderBottomColor: "#eef3f0",
    paddingVertical: 8,
  },
  card: {
    backgroundColor: "#f1f7f3",
    borderRadius: 10,
    padding: 12,
    gap: 4,
  },
  rowTitle: { fontWeight: "600", color: "#22302a" },
  muted: { color: "#4a5b52" },
  syncButton: {
    backgroundColor: "#0f6b46",
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  syncDisabled: { backgroundColor: "#9bb8aa" },
  syncText: { color: "#ffffff", fontWeight: "600" },
});
