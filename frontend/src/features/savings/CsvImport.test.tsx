// SPDX-License-Identifier: MIT
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { describe, expect, it, vi } from "vitest";

import { CsvImport } from "./CsvImport";

function csvFile(contents: string, name = "trips.csv"): File {
  return new File([contents], name, { type: "text/csv" });
}

describe("CsvImport", () => {
  it("matches columns flexibly and imports normalised rows", async () => {
    const onImport = vi.fn();
    render(<CsvImport onImport={onImport} pending={false} />);

    // Header uses aliases (`trip_date`, `distance`, `occupants`) rather than the
    // canonical column names — the parser should still recognise them.
    const file = csvFile("trip_date,distance,occupants\n2026-06-01,12,3\n");
    await userEvent.upload(screen.getByLabelText(/csv file/i), file);

    await screen.findByText(/rows ready/i);
    await userEvent.click(screen.getByRole("button", { name: /import 1 rows/i }));

    expect(onImport).toHaveBeenCalledWith([
      { date: "2026-06-01", distance_km: 12, passengers: 3 },
    ]);
  });

  it("accepts a row with no date column and renders a placeholder", async () => {
    const onImport = vi.fn();
    render(<CsvImport onImport={onImport} pending={false} />);

    // No `date` column at all: the field is optional and the preview shows a
    // placeholder rather than crashing on the missing value.
    const file = csvFile("distance_km,passengers\n18,4\n");
    await userEvent.upload(screen.getByLabelText(/csv file/i), file);

    await screen.findByText(/rows ready/i);
    expect(screen.getByRole("cell", { name: "—" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /import 1 rows/i }));
    expect(onImport).toHaveBeenCalledWith([{ distance_km: 18, passengers: 4 }]);
  });

  it("caps the import at 500 rows and reports the rest as skipped", async () => {
    const onImport = vi.fn();
    render(<CsvImport onImport={onImport} pending={false} />);

    const rows = Array.from(
      { length: 501 },
      (_, i) => `2026-06-01,${i + 1},2`,
    ).join("\n");
    const file = csvFile(`date,distance_km,passengers\n${rows}\n`);
    await userEvent.upload(screen.getByLabelText(/csv file/i), file);

    await waitFor(() =>
      expect(
        screen.getByText(
          (_content, el) => el?.textContent === "500 rows ready, 1 skipped.",
        ),
      ).toBeInTheDocument(),
    );
  });

  it("shows an error when no valid carpool rows are found", async () => {
    render(<CsvImport onImport={vi.fn()} pending={false} />);

    // passengers=1 fails the carpool minimum; the row is rejected.
    const file = csvFile("date,distance_km,passengers\n2026-06-01,10,1\n");
    await userEvent.upload(screen.getByLabelText(/csv file/i), file);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/no valid carpool rows/i);
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<CsvImport onImport={vi.fn()} pending={false} />);
    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results).toHaveNoViolations();
  });
});
