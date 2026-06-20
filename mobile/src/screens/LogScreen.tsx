// SPDX-License-Identifier: MIT
/**
 * Log screen: capture a transport footprint entry.
 *
 * Validates input with the shared zod schema (one contract with web/backend),
 * then hands the entry to the offline-first queue — which submits immediately
 * when online or saves it for sync on reconnect. Includes the consented,
 * opt-in assisted-capture card. All interactive elements expose screen-reader
 * labels/roles.
 */

import { useState } from "react";
import {
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  Pressable,
  View,
} from "react-native";
import {
  footprintRequestSchema,
  TRANSPORT_MODES,
  TRANSPORT_MODE_LABELS,
  type FootprintResponse,
  type TransportMode,
} from "@carbon/shared-types";

import { SignInBar } from "../auth/SignInBar";
import { ConsentDeniedError } from "../capture/consent";
import { useConsent } from "../capture/ConsentContext";
import { useLogQueue } from "../offline/QueueContext";

export function LogScreen() {
  const { online, submitLog, pending } = useLogQueue();
  const [mode, setMode] = useState<TransportMode>("car");
  const [distance, setDistance] = useState("");
  const [passengers, setPassengers] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<FootprintResponse | null>(null);

  async function handleSubmit() {
    setError(null);
    setStatus(null);
    setResult(null);

    const parsed = footprintRequestSchema.safeParse({
      domain: "transport",
      mode,
      distance_km: Number(distance),
      passengers: Number(passengers),
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input.");
      return;
    }

    const response = await submitLog(parsed.data);
    if (response) {
      setResult(response);
      setStatus("Logged and synced.");
    } else {
      setStatus(
        online
          ? "Saved. Sync is in progress…"
          : "You're offline — saved and will sync automatically when you reconnect.",
      );
    }
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <SignInBar />

      <View
        style={[styles.banner, online ? styles.bannerOnline : styles.bannerOffline]}
        accessibilityRole="text"
        accessibilityLabel={
          online ? "Status: online" : "Status: offline, entries are queued"
        }
      >
        <Text style={styles.bannerText}>
          {online ? "Online" : "Offline — entries are queued"}
          {pending.length > 0 ? `  ·  ${pending.length} pending` : ""}
        </Text>
      </View>

      <Text style={styles.label} accessibilityRole="header">
        Transport mode
      </Text>
      <View style={styles.modeRow}>
        {TRANSPORT_MODES.map((option) => {
          const selected = option === mode;
          return (
            <Pressable
              key={option}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              accessibilityLabel={`Mode: ${TRANSPORT_MODE_LABELS[option]}`}
              style={[styles.chip, selected && styles.chipSelected]}
              onPress={() => setMode(option)}
            >
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
                {TRANSPORT_MODE_LABELS[option]}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.label}>Distance (km)</Text>
      <TextInput
        style={styles.input}
        accessibilityLabel="Distance in kilometres"
        keyboardType="decimal-pad"
        placeholder="e.g. 12.5"
        value={distance}
        onChangeText={setDistance}
      />

      <Text style={styles.label}>Passengers</Text>
      <TextInput
        style={styles.input}
        accessibilityLabel="Number of passengers"
        keyboardType="number-pad"
        value={passengers}
        onChangeText={setPassengers}
      />

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Log this trip"
        style={styles.submit}
        onPress={() => void handleSubmit()}
      >
        <Text style={styles.submitText}>Log trip</Text>
      </Pressable>

      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
      {status ? (
        <Text style={styles.status} accessibilityRole="text">
          {status}
        </Text>
      ) : null}

      {result ? (
        <View style={styles.resultCard} accessibilityRole="summary">
          <Text style={styles.resultValue}>
            {result.kg_co2e.toFixed(2)} kg CO2e
          </Text>
          <Text style={styles.resultMessage}>{result.insight.message}</Text>
          <Text style={styles.resultBenchmark}>{result.insight.benchmark}</Text>
        </View>
      ) : null}

      <CaptureCard
        onCaptured={(capturedMode, distanceKm) => {
          setMode(capturedMode);
          setDistance(String(distanceKm));
          setStatus("Filled from assisted capture — review and log.");
        }}
      />
    </ScrollView>
  );
}

function CaptureCard({
  onCaptured,
}: {
  onCaptured: (mode: TransportMode, distanceKm: number) => void;
}) {
  const { consent, canCaptureTransport, grant, revoke, captureTransport } =
    useConsent();
  const [note, setNote] = useState<string | null>(null);

  async function handleCapture() {
    setNote(null);
    try {
      const trip = await captureTransport("car");
      onCaptured(trip.mode, trip.distanceKm);
      setNote(trip.assist);
    } catch (caught) {
      if (caught instanceof ConsentDeniedError) {
        setNote("Capture needs location consent and permission.");
      } else {
        setNote("Could not capture this trip.");
      }
    }
  }

  return (
    <View style={styles.captureCard}>
      <Text style={styles.label} accessibilityRole="header">
        Assisted transport capture (opt-in)
      </Text>
      <Text style={styles.muted}>
        Off by default. Uses location/Google Fit only after you turn this on and
        grant the OS permission. Revoke any time.
      </Text>
      <View style={styles.switchRow}>
        <Text style={styles.switchLabel}>Allow location-assisted capture</Text>
        <Switch
          accessibilityLabel="Allow location-assisted capture"
          value={consent.location}
          onValueChange={(next) =>
            void (next ? grant("location") : revoke("location"))
          }
        />
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Capture trip with assist"
        accessibilityState={{ disabled: !canCaptureTransport }}
        disabled={!canCaptureTransport}
        style={[styles.submit, !canCaptureTransport && styles.submitDisabled]}
        onPress={() => void handleCapture()}
      >
        <Text style={styles.submitText}>Capture trip</Text>
      </Pressable>
      {note ? (
        <Text style={styles.status} accessibilityRole="text">
          {note}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#ffffff" },
  content: { padding: 16, gap: 10 },
  banner: { borderRadius: 8, padding: 10 },
  bannerOnline: { backgroundColor: "#e3f3ea" },
  bannerOffline: { backgroundColor: "#fdeccf" },
  bannerText: { color: "#284c3b", fontWeight: "600" },
  label: { fontSize: 15, fontWeight: "600", color: "#22302a", marginTop: 6 },
  modeRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "#0f6b46",
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  chipSelected: { backgroundColor: "#0f6b46" },
  chipText: { color: "#0f6b46", fontWeight: "600" },
  chipTextSelected: { color: "#ffffff" },
  input: {
    borderWidth: 1,
    borderColor: "#c5d6cc",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  submit: {
    backgroundColor: "#0f6b46",
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 8,
  },
  submitDisabled: { backgroundColor: "#9bb8aa" },
  submitText: { color: "#ffffff", fontWeight: "700", fontSize: 16 },
  error: { color: "#b00020" },
  status: { color: "#284c3b" },
  resultCard: {
    backgroundColor: "#f1f7f3",
    borderRadius: 12,
    padding: 16,
    gap: 6,
    marginTop: 8,
  },
  resultValue: { fontSize: 22, fontWeight: "700", color: "#0f6b46" },
  resultMessage: { color: "#22302a" },
  resultBenchmark: { color: "#4a5b52" },
  captureCard: {
    borderWidth: 1,
    borderColor: "#e0e8e3",
    borderRadius: 12,
    padding: 16,
    gap: 8,
    marginTop: 16,
  },
  muted: { color: "#4a5b52" },
  switchRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  switchLabel: { color: "#22302a", flexShrink: 1, paddingRight: 12 },
});
