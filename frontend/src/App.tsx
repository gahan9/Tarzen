// SPDX-License-Identifier: MIT
import { FootprintPage } from "./features/footprint/FootprintPage";
import { RewardsPlaceholder } from "./features/rewards/RewardsPlaceholder";
import { LeaderboardPlaceholder } from "./features/leaderboard/LeaderboardPlaceholder";
import { SignInBar } from "./shared/auth/SignInBar";

export function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>

      <header className="app-header">
        <h1>Carbon Footprint</h1>
        <p className="app-tagline">Understand your impact. Reduce it, one trip at a time.</p>
        <SignInBar />
      </header>

      <main id="main" className="app-main" tabIndex={-1}>
        <FootprintPage />

        <aside className="app-roadmap" aria-label="Coming soon">
          <RewardsPlaceholder />
          <LeaderboardPlaceholder />
        </aside>
      </main>

      <footer className="app-footer">
        <p>Estimates use public emission factors and are for awareness, not billing.</p>
      </footer>
    </>
  );
}
