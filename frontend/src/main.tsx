// SPDX-License-Identifier: MIT
import * as React from "react";
import { StrictMode } from "react";
import * as ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { AuthProvider } from "./shared/auth/AuthContext";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found.");
}

async function enableAxeInDev(): Promise<void> {
  if (!import.meta.env.DEV) return;
  // Dev-only accessibility auditing: logs violations to the console during
  // development. Only the axe runtime is dynamically imported so it is left
  // out of production bundles; React/ReactDOM are already statically bundled.
  const axe = await import("@axe-core/react");
  await axe.default(React, ReactDOM, 1000);
}

void enableAxeInDev();

createRoot(rootElement).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
);
