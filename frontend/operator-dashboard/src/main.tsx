// Operator dashboard entry. Mounts the app shell; live feed + Mapbox are wired in Step 28.
import React from "react";
import { createRoot } from "react-dom/client";
import { RiskHeatmap } from "./components/RiskHeatmap";
import { CascadeChain } from "./components/CascadeChain";
import { StationDrilldown } from "./components/StationDrilldown";
import { connectLiveFeed } from "./lib/ws";

function App() {
  React.useEffect(() => {
    // Skeleton: WS is a no-op until services/api /ws/live exists (implementation-guide Step 26).
    connectLiveFeed((delta) => void delta);
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: 16, color: "#1f2937" }}>
      <header style={{ borderBottom: "1px solid #e5e7eb", paddingBottom: 12, marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>CascadeGuard — Operator Dashboard</h1>
        <p style={{ margin: "4px 0 0", color: "#b45309" }}>
          Skeleton shell · no live feed yet — wire up API + WS (Step 26) and Mapbox (Step 28).
        </p>
      </header>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        <RiskHeatmap />
        <div style={{ display: "grid", gap: 16 }}>
          <CascadeChain />
          <StationDrilldown />
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
