// SPDX-License-Identifier: MIT
/**
 * App shell: header + primary nav + routed main content. Routes are kept flat
 * and small; the footprint calculator is the home route, with savings,
 * leaderboard, and profile as siblings. The heavy 3D visualization is loaded
 * lazily inside the profile route, never in this shell bundle.
 */

import { Route, Routes } from "react-router-dom";

import { FootprintPage } from "./features/footprint/FootprintPage";
import { SavingsPage } from "./features/savings/SavingsPage";
import { LeaderboardPage } from "./features/leaderboard/LeaderboardPage";
import { ProfilePage } from "./features/profile/ProfilePage";
import { SignInBar } from "./shared/auth/SignInBar";
import { NavBar } from "./shared/ui/NavBar";

export function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>

      <header className="app-header">
        <h1>Carbon Footprint</h1>
        <p className="app-tagline">
          Understand your impact. Save more, one trip at a time.
        </p>
        <SignInBar />
        <NavBar />
      </header>

      <main id="main" className="app-main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<FootprintPage />} />
          <Route path="/savings" element={<SavingsPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="*"
            element={
              <section className="placeholder-card">
                <h2>Page not found</h2>
                <p>That route doesn&apos;t exist. Use the navigation above.</p>
              </section>
            }
          />
        </Routes>
      </main>

      <footer className="app-footer">
        <p>Estimates use public emission factors and are for awareness, not billing.</p>
      </footer>
    </>
  );
}
