// Corridor risk heatmap. Stations sit along the rail line (PNBE → MGS → BSB); each node is
// coloured by live cascade risk (green→amber→red), pulses when high, and greys out with no/stale
// data — an absence of data never reads as "safe". Click a node to drive the drill-down.
//
// A self-contained line diagram (no Mapbox token needed) so the dashboard runs with zero config;
// a Mapbox GL layer keyed on the same per-station risk can drop in for a geographic view.
import React from "react";
import { c, CORRIDOR, riskTone } from "../theme";
import type { StationMap } from "../main";
import type { FeedStatus } from "../lib/ws";

interface Props {
  stations: StationMap;
  selected: string | null;
  onSelect: (code: string | null) => void;
  status: FeedStatus;
}

const STALE_AFTER_S = 120;

export function RiskHeatmap({ stations, selected, onSelect, status }: Props) {
  const anyData = CORRIDOR.some((s) => stations[s.code]?.cascade_risk != null);

  return (
    <section style={styles.panel}>
      <div style={styles.head}>
        <h2 style={styles.title}>Cascade Risk Heatmap</h2>
        <Legend />
      </div>

      <div style={styles.map}>
        {/* rail line */}
        <div style={styles.rail} />
        {CORRIDOR.map((st) => {
          const d = stations[st.code];
          const stale = d != null && (d.mode !== "live" || d.data_age_s > STALE_AFTER_S);
          const tone = riskTone(stale ? null : d?.cascade_risk ?? null);
          const isSel = selected === st.code;
          const size = isSel ? 30 : 24;
          return (
            <button
              key={st.code}
              onClick={() => onSelect(isSel ? null : st.code)}
              style={{ ...styles.node, left: `${st.x * 100}%` }}
              title={`${st.name} (${st.code})`}
            >
              <span style={{ position: "relative", width: 30, height: 30, display: "grid", placeItems: "center" }}>
                {tone.level === "high" && <span className="cg-pulse" style={{ background: tone.fill }} />}
                <span
                  style={{
                    width: size,
                    height: size,
                    borderRadius: "50%",
                    background: tone.fill,
                    boxShadow: `0 0 0 ${isSel ? 4 : 0}px ${tone.fill}55, 0 0 22px ${tone.glow}`,
                    border: `2px solid ${isSel ? "#fff" : "rgba(255,255,255,0.25)"}`,
                    transition: "all 0.25s ease",
                  }}
                />
              </span>
              <span style={styles.code}>{st.code}</span>
              <span style={styles.name}>{st.name}</span>
              <span style={{ ...styles.riskTag, color: tone.fill }}>
                {d?.cascade_risk != null && !stale ? `${Math.round(d.cascade_risk * 100)}%` : stale ? "stale" : "—"}
              </span>
            </button>
          );
        })}

        {!anyData && (
          <div style={styles.overlay}>
            {status === "live" ? "Awaiting cascade snapshot…" : "Waiting for live feed — start services/api, then inject a delay."}
          </div>
        )}
      </div>
    </section>
  );
}

function Legend() {
  const items: [string, string][] = [
    ["Low", c.green],
    ["Elevated", c.amber],
    ["High", c.red],
    ["No data", c.grey],
  ];
  return (
    <div style={styles.legend}>
      {items.map(([label, color]) => (
        <span key={label} style={styles.legendItem}>
          <span style={{ width: 10, height: 10, borderRadius: 5, background: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    background: c.panel,
    border: `1px solid ${c.border}`,
    borderRadius: 16,
    padding: 20,
    display: "flex",
    flexDirection: "column",
    minHeight: 420,
  },
  head: { display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 },
  title: { margin: 0, fontSize: 16, fontWeight: 800 },
  legend: { display: "flex", gap: 14, flexWrap: "wrap" },
  legendItem: { display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: c.textMute, fontWeight: 600 },
  map: { position: "relative", flex: 1, marginTop: 28 },
  rail: {
    position: "absolute",
    left: "10%",
    right: "10%",
    top: "50%",
    height: 4,
    transform: "translateY(-50%)",
    background: `linear-gradient(90deg, ${c.borderSoft}, ${c.border}, ${c.borderSoft})`,
    borderRadius: 2,
  },
  node: {
    position: "absolute",
    top: "50%",
    transform: "translate(-50%, -50%)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
    background: "transparent",
    border: "none",
    cursor: "pointer",
    color: c.text,
  },
  code: { marginTop: 8, fontSize: 13, fontWeight: 800, fontFamily: "ui-monospace, Menlo, monospace" },
  name: { fontSize: 11, color: c.textFaint, fontWeight: 600 },
  riskTag: { fontSize: 13, fontWeight: 900 },
  overlay: {
    position: "absolute",
    inset: 0,
    display: "grid",
    placeItems: "center",
    color: c.textFaint,
    fontSize: 13,
    fontWeight: 600,
    textAlign: "center",
    padding: 16,
  },
};
