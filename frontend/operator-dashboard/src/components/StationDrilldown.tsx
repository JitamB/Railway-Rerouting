// Per-station drill-down for the selected node: cascade risk, the calibrated delay interval, the
// incoming at-risk trains, the "why", and the staleness watermark. Presentational — fed by the
// snapshot the shell already fetched (/stations/{code}).
import React from "react";
import { c, CORRIDOR, riskTone } from "../theme";
import type { StationView } from "../lib/api";
import type { CascadeDelta } from "../lib/ws";

interface Props {
  code: string | null;
  view: StationView | undefined;
  delta: CascadeDelta | undefined;
}

export function StationDrilldown({ code, view, delta }: Props) {
  const name = CORRIDOR.find((s) => s.code === code)?.name;
  const risk = view?.cascade_risk ?? delta?.cascade_risk ?? null;
  const tone = riskTone(risk);
  const interval = view?.delay_interval_min ?? delta?.delay_interval_min;

  return (
    <section style={styles.panel}>
      <h2 style={styles.title}>Station Drill-down</h2>

      {!code ? (
        <p style={styles.empty}>Select a station on the map to inspect at-risk trains and arrival windows.</p>
      ) : (
        <div className="fade-up">
          <div style={styles.header}>
            <div>
              <div style={styles.code}>{code}</div>
              <div style={styles.name}>{name}</div>
            </div>
            <div style={{ ...styles.riskBadge, background: `${tone.fill}1f`, color: tone.fill, borderColor: `${tone.fill}55` }}>
              {risk != null ? `${Math.round(risk * 100)}%` : "—"} {tone.label}
            </div>
          </div>

          {interval && (
            <div style={styles.metric}>
              <span style={styles.metricLabel}>Est. delay window</span>
              <span style={styles.metricValue}>
                {Math.round(interval[0])}–{Math.round(interval[1])} min
              </span>
            </div>
          )}

          <div style={styles.metric}>
            <span style={styles.metricLabel}>Incoming trains</span>
            <span style={styles.trains}>
              {view?.incoming_trains?.length
                ? view.incoming_trains.map((t) => (
                    <span key={t} style={styles.trainChip}>
                      {t}
                    </span>
                  ))
                : "—"}
            </span>
          </div>

          {view?.why && (
            <div style={styles.whyBox}>
              <span style={styles.metricLabel}>Why</span>
              <p style={styles.why}>{view.why}</p>
            </div>
          )}

          <div style={styles.footer}>
            <span style={{ ...styles.dot, background: (view?.mode ?? delta?.mode) === "live" ? c.green : c.amber }} />
            {view?.watermark ?? (delta ? `based on data ${Math.round(delta.data_age_s)}s old` : "no reading")}
          </div>
        </div>
      )}
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: { background: c.panel, border: `1px solid ${c.border}`, borderRadius: 16, padding: 20, flex: 1 },
  title: { margin: "0 0 14px", fontSize: 16, fontWeight: 800 },
  empty: { color: c.textFaint, fontSize: 13, fontWeight: 600, margin: 0 },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 },
  code: { fontSize: 24, fontWeight: 900, fontFamily: "ui-monospace, Menlo, monospace" },
  name: { fontSize: 13, color: c.textFaint, fontWeight: 600 },
  riskBadge: { border: "1px solid", borderRadius: 999, padding: "6px 12px", fontSize: 13, fontWeight: 800 },
  metric: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderTop: `1px solid ${c.borderSoft}`, gap: 12 },
  metricLabel: { fontSize: 11, color: c.textFaint, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 },
  metricValue: { fontSize: 15, fontWeight: 800, color: c.text },
  trains: { display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" },
  trainChip: {
    fontFamily: "ui-monospace, Menlo, monospace",
    fontSize: 12,
    fontWeight: 700,
    color: c.brand,
    background: `${c.brandDim}22`,
    border: `1px solid ${c.brandDim}55`,
    borderRadius: 6,
    padding: "2px 8px",
  },
  whyBox: { borderTop: `1px solid ${c.borderSoft}`, paddingTop: 10, marginTop: 4 },
  why: { fontSize: 13, color: c.textMute, fontWeight: 600, margin: "6px 0 0", lineHeight: 1.5 },
  footer: { display: "flex", alignItems: "center", gap: 8, marginTop: 16, fontSize: 12, color: c.textFaint, fontWeight: 600 },
  dot: { width: 8, height: 8, borderRadius: 4 },
};
