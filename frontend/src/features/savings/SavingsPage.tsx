// SPDX-License-Identifier: MIT
/**
 * Add-Savings page: a tabbed surface for the three capture paths — manual
 * entry, CSV carpool import, and verified ticket upload. Each tab owns its own
 * request lifecycle; on success a unified result card is shown and focused for
 * keyboard/screen-reader users. Points and verification are server-authoritative.
 */

import { useCallback, useMemo, useState } from "react";
import {
  type CarpoolImportRow,
  type SavingsRequest,
  type TicketExtraction,
} from "@carbon/shared-types";

import {
  importSavings,
  submitSavings,
  submitTicket,
} from "../../shared/api/savingsClient";
import { useAsyncFn } from "../../shared/hooks/useAsyncFn";
import { useAuth } from "../../shared/auth/useAuth";
import { useFocusOnChange } from "../../shared/a11y/useFocusOnChange";
import { Emoji } from "../../shared/ui/Emoji";
import { type EmojiKey } from "../../shared/ui/emojiMap";
import { ManualSavingsForm } from "./ManualSavingsForm";
import { CsvImport } from "./CsvImport";
import { TicketUpload } from "./TicketUpload";
import { SavingsResultCard, type SavingsSummary } from "./SavingsResultCard";

type Tab = "manual" | "import" | "ticket";

const TABS: ReadonlyArray<{ id: Tab; label: string; emoji: EmojiKey }> = [
  { id: "manual", label: "Manual", emoji: "manual" },
  { id: "import", label: "Import CSV", emoji: "import" },
  { id: "ticket", label: "Ticket", emoji: "ticket" },
];

function ExtractionDetails({ extraction }: { extraction: TicketExtraction }) {
  const rows: Array<[string, string]> = [];
  if (extraction.origin) rows.push(["From", extraction.origin]);
  if (extraction.destination) rows.push(["To", extraction.destination]);
  if (extraction.mode) rows.push(["Mode", extraction.mode]);
  if (extraction.date) rows.push(["Date", extraction.date]);
  if (typeof extraction.fare === "number") {
    rows.push(["Fare", String(extraction.fare)]);
  }
  if (rows.length === 0) return null;
  return (
    <dl className="extraction-list">
      {rows.map(([label, value]) => (
        <div key={label} className="extraction-row">
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SavingsPage() {
  const { getIdToken } = useAuth();
  const [tab, setTab] = useState<Tab>("manual");

  const manual = useAsyncFn(
    useCallback(
      (signal: AbortSignal, request: SavingsRequest) =>
        submitSavings(request, { signal, getToken: getIdToken }),
      [getIdToken],
    ),
  );
  const csv = useAsyncFn(
    useCallback(
      (signal: AbortSignal, rows: CarpoolImportRow[]) =>
        importSavings(rows, { signal, getToken: getIdToken }),
      [getIdToken],
    ),
  );
  const ticket = useAsyncFn(
    useCallback(
      (signal: AbortSignal, file: File) =>
        submitTicket(file, { signal, getToken: getIdToken }),
      [getIdToken],
    ),
  );

  const summary: SavingsSummary | null = useMemo(() => {
    if (tab === "manual" && manual.state.status === "success") {
      const d = manual.state.data;
      return {
        title: "Saving logged",
        kgSaved: d.kg_co2e_saved,
        pointsAwarded: d.points_awarded,
        verified: d.verified,
        badgesUnlocked: d.badges_unlocked,
      };
    }
    if (tab === "import" && csv.state.status === "success") {
      const d = csv.state.data;
      return {
        title: `Imported ${d.rows_imported} trips`,
        kgSaved: d.total_kg_co2e_saved,
        pointsAwarded: d.points_awarded,
        verified: false,
        badgesUnlocked: d.badges_unlocked,
      };
    }
    if (tab === "ticket" && ticket.state.status === "success") {
      const d = ticket.state.data;
      return {
        title: "Ticket verified",
        kgSaved: d.kg_co2e_saved,
        pointsAwarded: d.points_awarded,
        verified: d.verified,
        badgesUnlocked: d.badges_unlocked,
      };
    }
    return null;
  }, [tab, manual.state, csv.state, ticket.state]);

  const active =
    tab === "manual" ? manual : tab === "import" ? csv : ticket;
  const focusKey =
    active.state.status === "success" || active.state.status === "error"
      ? `${tab}-${active.state.status}`
      : null;
  const resultRef = useFocusOnChange<HTMLElement>(focusKey);

  const ticketExtraction =
    tab === "ticket" && ticket.state.status === "success"
      ? ticket.state.data.extraction
      : undefined;

  return (
    <div className="savings-layout">
      <section aria-labelledby="savings-heading">
        <h1 id="savings-heading">
          <Emoji name="savings" /> Add carbon savings
        </h1>
        <p className="app-tagline">
          Log the lower-carbon choices you made instead of driving solo.
        </p>

        <div className="tabs" role="tablist" aria-label="Savings entry method">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`tab-${item.id}`}
              aria-selected={tab === item.id}
              aria-controls={`panel-${item.id}`}
              className={tab === item.id ? "tab tab--active" : "tab"}
              onClick={() => setTab(item.id)}
            >
              <Emoji name={item.emoji} /> {item.label}
            </button>
          ))}
        </div>

        <div
          id={`panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`tab-${tab}`}
          className="tab-panel"
        >
          {tab === "manual" ? (
            <ManualSavingsForm
              onSubmit={(request) => void manual.run(request)}
              pending={manual.state.status === "loading"}
            />
          ) : null}
          {tab === "import" ? (
            <CsvImport
              onImport={(rows) => void csv.run(rows)}
              pending={csv.state.status === "loading"}
            />
          ) : null}
          {tab === "ticket" ? (
            <TicketUpload
              onSubmit={(file) => void ticket.run(file)}
              pending={ticket.state.status === "loading"}
            />
          ) : null}
        </div>
      </section>

      <div aria-live="polite" className="savings-outcome">
        {active.state.status === "error" ? (
          <section
            ref={resultRef}
            tabIndex={-1}
            role="alert"
            className="result-error"
            aria-labelledby="savings-error-heading"
          >
            <h2 id="savings-error-heading">We couldn&apos;t save that</h2>
            <p>{active.state.message}</p>
            {active.state.requestId ? (
              <p className="result-error-id">Reference: {active.state.requestId}</p>
            ) : null}
          </section>
        ) : null}

        {summary ? (
          <>
            <SavingsResultCard ref={resultRef} summary={summary} />
            {ticketExtraction ? (
              <ExtractionDetails extraction={ticketExtraction} />
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
