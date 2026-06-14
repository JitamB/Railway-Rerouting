// Cascade-chain visualisation with the per-hop "why" (GNNExplainer attribution from /stations).
// e.g. 12301 → Mughal Sarai (89%) → Varanasi (87%), each hop coloured by risk with its driver.
import React from "react";
import { c, CORRIDOR, riskTone } from "../theme";
import type { StationMap, ViewMap } from "../main";

interface Props {
  stations: StationMap;
  views: ViewMap;
  selected: string | null;
  onSelect: (code: string | null) => void;
}

export function CascadeChain({ stations, views, selected, onSelect }: Props) {
  const hasData = CORRIDOR.some((s) => stations[s.code]?.cascade_risk != null);

  return (
    <section style={styles.panel}>
      <h2 style={styles.title}>Cascade Chain</h2>
      {!hasData ? (
        <p style={styles.empty}>The propagation path renders here once the live feed reports risk.</p>
      ) : (
        <div style={styles.chain}>
          {CORRIDOR.map((st, i) => {
            const d = stations[st.code];
            const tone = riskTone(d?.cascade_risk ?? null);
            const why = views[st.code]?.why;
            const interval = d?.delay_interval_min;
            const isSel = selected === st.code;
            return (
              <React.Fragment key={st.code}>
                {i > 0 && (
                  <div style={styles.arrowWrap}>
                    <div style={styles.arrowLine} />
                    <span style={styles.arrowHead}>▸</span>
                  </div>
                )}
                <button
                  onClick={() => onSelect(isSel ? null : st.code)}
                  className="fade-up"
                  style={{ ...styles.hop, borderColor: isSel ? tone.fill : c.borderSoft, background: isSel ? `${tone.fill}14` : c.panelAlt }}
                >
                  <div style={styles.hopHeader}>
                    <span style={styles.hopName}>
                      <span style={styles.hopCode}>{st.code}</span> {st.name}
                    </span>
                    <span style={{ ...styles.hopRisk, color: tone.fill }}>
                      {d?.cascade_risk != null ? `${Math.round(d.cascade_risk * 100)}%` : "—"}
                    </span>
                  </div>
                  {interval && (
                    <div style={styles.hopInterval}>
                      delay {Math.round(interval[0])}–{Math.round(interval[1])} min
                    </div>
                  )}
                  {why && <div style={styles.hopWhy}>↳ {why}</div>}
                </button>
              </React.Fragment>
            );
          })}
        </div>
      )}
    </section>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: { background: c.panel, border: `1px solid ${c.border}`, borderRadius: 16, padding: 20 },
  title: { margin: "0 0 14px", fontSize: 16, fontWeight: 800 },
  empty: { color: c.textFaint, fontSize: 13, fontWeight: 600, margin: 0 },
  chain: { display: "flex", flexDirection: "column" },
  hop: {
    textAlign: "left",
    border: "1px solid",
    borderRadius: 12,
    padding: "12px 14px",
    cursor: "pointer",
    color: c.text,
    transition: "all 0.2s ease",
  },
  hopHeader: { display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10 },
  hopName: { fontSize: 14, fontWeight: 700, color: c.text },
  hopCode: { fontFamily: "ui-monospace, Menlo, monospace", fontWeight: 800, color: c.textMute },
  hopRisk: { fontSize: 18, fontWeight: 900 },
  hopInterval: { fontSize: 12, color: c.textMute, fontWeight: 600, marginTop: 4 },
  hopWhy: { fontSize: 12, color: c.textFaint, fontWeight: 600, marginTop: 4 },
  arrowWrap: { display: "flex", flexDirection: "column", alignItems: "center", height: 22, justifyContent: "center" },
  arrowLine: { width: 2, height: 10, background: c.border },
  arrowHead: { color: c.border, transform: "rotate(90deg)", fontSize: 12, lineHeight: 0 },
};
