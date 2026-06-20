// SPDX-License-Identifier: MIT
/**
 * Transport footprint input form (Phase 3, domain = transport).
 *
 * Client-side validation uses the shared zod schema so the same rules guard
 * the UI and the network boundary. Every input has an associated <label>,
 * errors are announced via `role="alert"` and linked with `aria-describedby`,
 * and the submit button reflects the pending state.
 */

import { useId, useState, type FormEvent } from "react";
import {
  footprintRequestSchema,
  TRANSPORT_MODES,
  TRANSPORT_MODE_LABELS,
  type FootprintRequest,
  type TransportMode,
} from "@carbon/shared-types";

interface FootprintFormProps {
  onSubmit: (request: FootprintRequest) => void;
  pending: boolean;
}

/** Short, mode-specific helper copy. Exhaustive over {@link TransportMode}. */
function modeHint(mode: TransportMode): string {
  switch (mode) {
    case "car":
      return "Tip: add passengers to split the footprint per person.";
    case "bus":
      return "Buses spread emissions across many riders.";
    case "rail":
      return "Rail is typically the lowest-carbon motorised option.";
    case "flight":
      return "Long flights dominate most personal footprints.";
    default: {
      const _exhaustive: never = mode;
      return _exhaustive;
    }
  }
}

export function FootprintForm({ onSubmit, pending }: FootprintFormProps) {
  const [mode, setMode] = useState<TransportMode>("car");
  const [distance, setDistance] = useState("");
  const [passengers, setPassengers] = useState("");
  const [error, setError] = useState<string | null>(null);

  const modeId = useId();
  const distanceId = useId();
  const passengersId = useId();
  const errorId = useId();
  const hintId = useId();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const candidate = {
      domain: "transport" as const,
      mode,
      distance_km: Number(distance),
      ...(passengers.trim() === "" ? {} : { passengers: Number(passengers) }),
    };

    const parsed = footprintRequestSchema.safeParse(candidate);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Please check your input.");
      return;
    }
    onSubmit(parsed.data);
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-describedby={hintId}>
      <h2>Estimate a trip</h2>
      <p id={hintId} className="form-hint">
        {modeHint(mode)}
      </p>

      <div className="field">
        <label htmlFor={modeId}>Mode of transport</label>
        <select
          id={modeId}
          value={mode}
          onChange={(event) => setMode(event.target.value as TransportMode)}
        >
          {TRANSPORT_MODES.map((option) => (
            <option key={option} value={option}>
              {TRANSPORT_MODE_LABELS[option]}
            </option>
          ))}
        </select>
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

      <div className="field">
        <label htmlFor={passengersId}>
          Passengers <span className="optional">(optional)</span>
        </label>
        <input
          id={passengersId}
          type="number"
          inputMode="numeric"
          min="1"
          step="1"
          value={passengers}
          onChange={(event) => setPassengers(event.target.value)}
        />
      </div>

      {error ? (
        <p id={errorId} role="alert" className="field-error">
          {error}
        </p>
      ) : null}

      <button type="submit" disabled={pending}>
        {pending ? "Calculating…" : "Calculate footprint"}
      </button>
    </form>
  );
}
