// SPDX-License-Identifier: MIT
/**
 * Manual savings entry: pick a low-carbon mode (carpool / bus / rail), enter
 * distance, and (for carpool) passenger count. Validated client-side with the
 * shared zod schema so the same rules guard the UI and the API boundary.
 */

import { useId, useState, type FormEvent } from "react";
import {
  SAVINGS_MODES,
  SAVINGS_MODE_LABELS,
  savingsRequestSchema,
  type SavingsMode,
  type SavingsRequest,
} from "@carbon/shared-types";

import { Emoji } from "../../shared/ui/Emoji";
import { type EmojiKey } from "../../shared/ui/emojiMap";

const MODE_EMOJI: Record<SavingsMode, EmojiKey> = {
  carpool: "carpool",
  bus: "bus",
  rail: "rail",
};

interface ManualSavingsFormProps {
  onSubmit: (request: SavingsRequest) => void;
  pending: boolean;
}

export function ManualSavingsForm({ onSubmit, pending }: ManualSavingsFormProps) {
  const [mode, setMode] = useState<SavingsMode>("carpool");
  const [distance, setDistance] = useState("");
  const [passengers, setPassengers] = useState("2");
  const [error, setError] = useState<string | null>(null);

  const modeId = useId();
  const distanceId = useId();
  const passengersId = useId();
  const errorId = useId();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const candidate = {
      source: "manual" as const,
      mode,
      distance_km: Number(distance),
      ...(mode === "carpool" ? { passengers: Number(passengers) } : {}),
    };

    const parsed = savingsRequestSchema.safeParse(candidate);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Please check your input.");
      return;
    }
    onSubmit(parsed.data);
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <h2>
        <Emoji name="manual" /> Log a saving
      </h2>

      <div className="field">
        <label htmlFor={modeId}>Low-carbon mode</label>
        <select
          id={modeId}
          value={mode}
          onChange={(event) => setMode(event.target.value as SavingsMode)}
        >
          {SAVINGS_MODES.map((option) => (
            <option key={option} value={option}>
              {SAVINGS_MODE_LABELS[option]}
            </option>
          ))}
        </select>
        <p className="form-hint">
          <Emoji name={MODE_EMOJI[mode]} />{" "}
          {mode === "carpool"
            ? "Saving vs everyone driving solo."
            : "Saving vs driving the same distance solo."}
        </p>
      </div>

      <div className="field">
        <label htmlFor={distanceId}>Distance (km)</label>
        <input
          id={distanceId}
          type="number"
          inputMode="decimal"
          min="0"
          step="any"
          required
          value={distance}
          onChange={(event) => setDistance(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
        />
      </div>

      {mode === "carpool" ? (
        <div className="field">
          <label htmlFor={passengersId}>Passengers (including you)</label>
          <input
            id={passengersId}
            type="number"
            inputMode="numeric"
            min="2"
            step="1"
            value={passengers}
            onChange={(event) => setPassengers(event.target.value)}
          />
        </div>
      ) : null}

      {error ? (
        <p id={errorId} role="alert" className="field-error">
          {error}
        </p>
      ) : null}

      <button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Add saving"}
      </button>
    </form>
  );
}
