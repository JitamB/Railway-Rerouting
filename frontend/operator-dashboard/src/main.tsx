// Operator dashboard entry. Subscribes to the live WS feed, keeps a per-station risk map, and
// fetches the station snapshots (why + incoming trains) used by the chain and drill-down. An
// injected delay turns the corridor nodes amber/red live (implementation-guide Step 28).
import "./styles.css";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { RiskHeatmap } from "./components/RiskHeatmap";
import { CascadeChain } from "./components/CascadeChain";
import { StationDrilldown } from "./components/StationDrilldown";
import { connectLiveFeed, type CascadeDelta, type FeedStatus } from "./lib/ws";
import { getStation, type StationView } from "./lib/api";
import { c, CORRIDOR, riskTone } from "./theme";

export type StationMap = Record<string, CascadeDelta | undefined>;
export type ViewMap = Record<string, StationView | undefined>;

const STATUS_META: Record<FeedStatus, { color: string; label: string }> = {
  connecting: { color: c.amber, label: "Connecting" },
  live: { color: c.green, label: "Live" },
  offline: { color: c.red, label: "Offline" },
};

function App() {
  const seed = useMemo<StationMap>(() => Object.fromEntries(CORRIDOR.map((s) => [s.code, undefined])), []);
  const [stations, setStations] = useState<StationMap>(seed);
  const [views, setViews] = useState<ViewMap>({});
  const [status, setStatus] = useState<FeedStatus>("connecting");
  const [selected, setSelected] = useState<string | null>(null);

  const refreshViews = useCallback(async () => {
    const entries = await Promise.all(
      CORRIDOR.map(async (s) => {
        try {
          return [s.code, await getStation(s.code)] as const;
        } catch {
          return [s.code, undefined] as const;
        }
      }),
    );
    setViews(Object.fromEntries(entries));
  }, []);

  useEffect(() => {
    const dispose = connectLiveFeed({
      onStatus: setStatus,
      onDelta: (d) => setStations((prev) => ({ ...prev, [d.station]: d })),
      onComplete: () => void refreshViews(),
    });
    return dispose;
  }, [refreshViews]);

  const risks = CORRIDOR.map((s) => stations[s.code]?.cascade_risk).filter((r): r is number => r != null);
  const maxRisk = risks.length ? Math.max(...risks) : null;
  const tone = riskTone(maxRisk);
  const ages = Object.values(stations)
    .map((s) => s?.data_age_s)
    .filter((a): a is number => a != null);
  const dataAge = ages.length ? Math.max(...ages) : null;
  const sm = STATUS_META[status];

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.brand}>
          <span style={styles.logo}>🚆</span>
          <div>
            <div style={styles.brandName}>CascadeGuard</div>
            <div style={styles.brandSub}>Operator Console · Corridor Watch</div>
          </div>
        </div>
        <div style={styles.headerRight}>
          {maxRisk != null && (
            <div style={{ ...styles.healthChip, background: `${tone.fill}1f`, borderColor: `${tone.fill}55` }}>
              <span style={{ ...styles.healthDot, background: tone.fill }} />
              <span style={{ color: tone.fill, fontWeight: 800 }}>{tone.label}</span>
              <span style={styles.healthPct}>peak {Math.round(maxRisk * 100)}%</span>
            </div>
          )}
          {dataAge != null && <span style={styles.watermark}>based on data {Math.round(dataAge)}s old</span>}
          <div style={styles.status}>
            <span
              style={{
                ...styles.statusDot,
                background: sm.color,
                animation: status === "live" ? "liveBlink 1.6s infinite" : undefined,
              }}
            />
            <span style={{ color: sm.color, fontWeight: 700 }}>{sm.label}</span>
          </div>
        </div>
      </header>

      <main style={styles.grid}>
        <RiskHeatmap stations={stations} selected={selected} onSelect={setSelected} status={status} />
        <div style={styles.col}>
          <CascadeChain stations={stations} views={views} onSelect={setSelected} selected={selected} />
          <StationDrilldown code={selected} view={selected ? views[selected] : undefined} delta={selected ? stations[selected] : undefined} />
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: { minHeight: "100%", display: "flex", flexDirection: "column" },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px 24px",
    borderBottom: `1px solid ${c.border}`,
    background: "rgba(13,20,36,0.6)",
    backdropFilter: "blur(8px)",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  brand: { display: "flex", alignItems: "center", gap: 12 },
  logo: { fontSize: 26 },
  brandName: { fontSize: 18, fontWeight: 900, letterSpacing: -0.3 },
  brandSub: { fontSize: 12, color: c.textFaint, fontWeight: 600, letterSpacing: 0.3 },
  headerRight: { display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" },
  healthChip: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 12px",
    borderRadius: 999,
    border: "1px solid",
    fontSize: 13,
  },
  healthDot: { width: 8, height: 8, borderRadius: 4 },
  healthPct: { color: c.textMute, fontWeight: 700, fontSize: 12 },
  watermark: { color: c.textFaint, fontSize: 12, fontWeight: 600 },
  status: { display: "flex", alignItems: "center", gap: 8, fontSize: 13 },
  statusDot: { width: 9, height: 9, borderRadius: 5 },
  grid: { flex: 1, display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: 18, padding: 24 },
  col: { display: "flex", flexDirection: "column", gap: 18, minWidth: 0 },
};

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
