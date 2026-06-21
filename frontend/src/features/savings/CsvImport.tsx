// SPDX-License-Identifier: MIT
/**
 * CSV carpool import. Parses a trip-history export entirely in the browser with
 * papaparse, validates each row against the shared zod contract, previews the
 * accepted rows, and only then submits the batch. Column names are matched
 * flexibly (e.g. `distance` or `distance_km`) so common exports just work.
 */

import { useId, useRef, useState, type ChangeEvent } from "react";
import Papa from "papaparse";
import {
  carpoolImportRowSchema,
  type CarpoolImportRow,
} from "@carbon/shared-types";

import { Emoji } from "../../shared/ui/Emoji";

interface CsvImportProps {
  onImport: (rows: CarpoolImportRow[]) => void;
  pending: boolean;
}

interface ParseOutcome {
  rows: CarpoolImportRow[];
  skipped: number;
}

const MAX_ROWS = 500;

function pick(row: Record<string, unknown>, keys: string[]): unknown {
  for (const key of keys) {
    const match = Object.keys(row).find(
      (k) => k.trim().toLowerCase() === key,
    );
    if (match !== undefined) return row[match];
  }
  return undefined;
}

function toNumber(value: unknown): number {
  return typeof value === "number" ? value : Number(String(value ?? "").trim());
}

function normaliseRow(raw: Record<string, unknown>): CarpoolImportRow | null {
  const candidate = {
    date: pick(raw, ["date", "trip_date", "day"]),
    distance_km: toNumber(pick(raw, ["distance_km", "distance", "km"])),
    passengers: toNumber(pick(raw, ["passengers", "occupants", "riders"])),
  };
  const parsed = carpoolImportRowSchema.safeParse({
    ...candidate,
    date: candidate.date === undefined ? undefined : String(candidate.date),
  });
  return parsed.success ? parsed.data : null;
}

const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 1,
});

export function CsvImport({ onImport, pending }: CsvImportProps) {
  const [outcome, setOutcome] = useState<ParseOutcome | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const errorId = useId();

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setError(null);
    setOutcome(null);
    if (!file) return;

    Papa.parse<Record<string, unknown>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const accepted: CarpoolImportRow[] = [];
        let skipped = 0;
        for (const raw of results.data) {
          const row = normaliseRow(raw);
          if (row && accepted.length < MAX_ROWS) accepted.push(row);
          else skipped += 1;
        }
        if (accepted.length === 0) {
          setError(
            "No valid carpool rows found. Expected columns: date, distance_km, passengers (>= 2).",
          );
          return;
        }
        setOutcome({ rows: accepted, skipped });
      },
      error: () => setError("That file could not be parsed as CSV."),
    });
  }

  function handleImport() {
    if (outcome) onImport(outcome.rows);
  }

  return (
    <div>
      <h2>
        <Emoji name="import" /> Import carpool history
      </h2>
      <p className="form-hint">
        Upload a CSV with <code>date</code>, <code>distance_km</code>, and{" "}
        <code>passengers</code> columns. Parsing happens in your browser.
      </p>

      <div className="field">
        <label htmlFor={inputId}>CSV file</label>
        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={handleFile}
          aria-describedby={error ? errorId : undefined}
        />
      </div>

      {error ? (
        <p id={errorId} role="alert" className="field-error">
          {error}
        </p>
      ) : null}

      {outcome ? (
        <div className="csv-preview">
          <p>
            <strong>{outcome.rows.length}</strong> rows ready
            {outcome.skipped > 0 ? `, ${outcome.skipped} skipped` : ""}.
          </p>
          <table className="csv-table">
            <caption className="visually-hidden-caption">
              Preview of the first rows to import
            </caption>
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Distance (km)</th>
                <th scope="col">Passengers</th>
              </tr>
            </thead>
            <tbody>
              {outcome.rows.slice(0, 5).map((row, index) => (
                <tr key={`${row.date ?? "row"}-${index}`}>
                  <td>{row.date ?? "—"}</td>
                  <td>{numberFormat.format(row.distance_km)}</td>
                  <td>{row.passengers}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {outcome.rows.length > 5 ? (
            <p className="form-hint">
              Showing 5 of {outcome.rows.length} rows.
            </p>
          ) : null}

          <button type="button" onClick={handleImport} disabled={pending}>
            {pending ? "Importing…" : `Import ${outcome.rows.length} rows`}
          </button>
        </div>
      ) : null}
    </div>
  );
}
