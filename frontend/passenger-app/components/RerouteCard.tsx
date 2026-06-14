// The re-route card — the product's centrepiece. Shows the live cascade risk, the calibrated
// delay interval, capacity-checked alternatives (with seat reality), the one-line "why", and the
// staleness watermark. Safety-critical fields (train no., platform, time, seats) render straight
// from structured data — never from LLM prose. The plain-language guidance is the only generated
// text, and it sits clearly apart.
import { View, Text, StyleSheet } from "react-native";
import { colors, radius, shadow, space, type, riskStyle } from "../lib/theme";
import type { RerouteOption } from "../lib/api";

export interface RerouteCardData {
  trainNo: string;
  route: string; // "PNBE → BSB"
  riskPct: number; // 0..100
  delayInterval: [number, number]; // minutes
  why: string;
  guidance: string;
  options: RerouteOption[];
  watermark: string;
  mode: string;
}

function seatTone(status: string): { fg: string; bg: string } {
  const s = status.toUpperCase();
  if (s.startsWith("AVL")) return { fg: colors.green, bg: colors.greenBg };
  if (s.startsWith("WL") || s.startsWith("TATKAL")) return { fg: colors.amber, bg: colors.amberBg };
  return { fg: colors.red, bg: colors.redBg }; // FULL
}

function RiskMeter({ pct, fg }: { pct: number; fg: string }) {
  return (
    <View style={styles.meterTrack}>
      <View style={[styles.meterFill, { width: `${Math.min(100, Math.max(4, pct))}%`, backgroundColor: fg }]} />
    </View>
  );
}

export function RerouteCard({ data }: { data: RerouteCardData }) {
  const risk = riskStyle(data.riskPct / 100);
  const [lo, hi] = data.delayInterval;

  return (
    <View style={[styles.card, shadow.raised, { borderColor: risk.bg }]}>
      {/* accent rail */}
      <View style={[styles.rail, { backgroundColor: risk.fg }]} />

      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={type.label}>YOUR TRAIN</Text>
          <Text style={styles.train}>{data.trainNo}</Text>
          <Text style={styles.route}>{data.route}</Text>
        </View>
        <View style={[styles.riskPill, { backgroundColor: risk.bg }]}>
          <Text style={[styles.riskPillLabel, { color: risk.fg }]}>{risk.label} risk</Text>
          <Text style={[styles.riskPct, { color: risk.fg }]}>{Math.round(data.riskPct)}%</Text>
        </View>
      </View>

      <RiskMeter pct={data.riskPct} fg={risk.fg} />

      <View style={styles.intervalRow}>
        <Text style={styles.intervalText}>
          Likely delay <Text style={styles.intervalStrong}>{Math.round(lo)}–{Math.round(hi)} min</Text>
        </Text>
        <Text style={styles.why}>· {data.why}</Text>
      </View>

      {/* alternatives */}
      <Text style={[type.label, { marginTop: space(4), marginBottom: space(2) }]}>
        {data.options.length ? "FEASIBLE ALTERNATIVES" : "NO ALTERNATIVE AVAILABLE"}
      </Text>
      {data.options.map((o, i) => {
        const tone = seatTone(o.seats_status);
        return (
          <View key={o.train_no} style={[styles.alt, i === 0 && styles.altBest]}>
            {i === 0 && (
              <View style={styles.bestTag}>
                <Text style={styles.bestTagText}>BEST</Text>
              </View>
            )}
            <View style={styles.altMain}>
              <Text style={styles.altTrain}>{o.train_no}</Text>
              <View style={styles.altMetaRow}>
                <Meta icon="P" value={o.platform} />
                <Meta icon="Dep" value={o.departs} />
                <Meta icon="Arr" value={o.arrives_dest} />
              </View>
            </View>
            <View style={[styles.seatBadge, { backgroundColor: tone.bg }]}>
              <Text style={[styles.seatText, { color: tone.fg }]}>{o.seats_status}</Text>
            </View>
          </View>
        );
      })}

      {/* generated guidance — clearly separated from the structured facts above */}
      {!!data.guidance && (
        <View style={styles.guidance}>
          <Text style={styles.guidanceText}>{data.guidance}</Text>
        </View>
      )}

      <View style={styles.footer}>
        <View style={[styles.dot, { backgroundColor: data.mode === "live" ? colors.green : colors.amber }]} />
        <Text style={styles.footerText}>
          {data.mode === "live" ? "Live" : data.mode.replace("_", " ")} · {data.watermark}
        </Text>
      </View>
    </View>
  );
}

function Meta({ icon, value }: { icon: string; value: string }) {
  return (
    <View style={styles.meta}>
      <Text style={styles.metaIcon}>{icon}</Text>
      <Text style={styles.metaValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    padding: space(5),
    overflow: "hidden",
  },
  rail: { position: "absolute", left: 0, top: 0, bottom: 0, width: 6 },
  header: { flexDirection: "row", alignItems: "flex-start", marginBottom: space(4) },
  train: { fontSize: 30, fontWeight: "900", color: colors.text, letterSpacing: -0.5, marginTop: 2 },
  route: { fontSize: 14, fontWeight: "700", color: colors.textMute, marginTop: 2 },
  riskPill: { alignItems: "center", paddingHorizontal: space(3.5), paddingVertical: space(2), borderRadius: radius.lg },
  riskPillLabel: { fontSize: 11, fontWeight: "800", letterSpacing: 0.4 },
  riskPct: { fontSize: 26, fontWeight: "900", letterSpacing: -0.5 },
  meterTrack: { height: 8, borderRadius: radius.pill, backgroundColor: colors.border, overflow: "hidden" },
  meterFill: { height: 8, borderRadius: radius.pill },
  intervalRow: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", marginTop: space(3) },
  intervalText: { fontSize: 14, fontWeight: "600", color: colors.textMute },
  intervalStrong: { color: colors.text, fontWeight: "800" },
  why: { fontSize: 13, fontWeight: "600", color: colors.textFaint, marginLeft: space(1) },
  alt: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space(3.5),
    marginBottom: space(2.5),
  },
  altBest: { borderColor: colors.brandSoft, backgroundColor: colors.brandTint },
  bestTag: {
    position: "absolute",
    top: -9,
    left: space(3.5),
    backgroundColor: colors.brandSoft,
    paddingHorizontal: space(2),
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  bestTagText: { color: colors.white, fontSize: 9, fontWeight: "900", letterSpacing: 0.8 },
  altMain: { flex: 1 },
  altTrain: { fontSize: 18, fontWeight: "900", color: colors.text, letterSpacing: -0.3 },
  altMetaRow: { flexDirection: "row", marginTop: space(1.5), gap: space(4) as number },
  meta: { flexDirection: "row", alignItems: "baseline", gap: 4 as number },
  metaIcon: { fontSize: 10, fontWeight: "800", color: colors.textFaint, letterSpacing: 0.3 },
  metaValue: { fontSize: 13, fontWeight: "700", color: colors.textMute },
  seatBadge: { paddingHorizontal: space(3), paddingVertical: space(1.5), borderRadius: radius.md },
  seatText: { fontSize: 12, fontWeight: "800" },
  guidance: {
    marginTop: space(3),
    backgroundColor: colors.brand,
    borderRadius: radius.lg,
    padding: space(4),
  },
  guidanceText: { color: "#E0E7FF", fontSize: 14, fontWeight: "600", lineHeight: 21 },
  footer: { flexDirection: "row", alignItems: "center", marginTop: space(4), gap: space(2) as number },
  dot: { width: 8, height: 8, borderRadius: 4 },
  footerText: { fontSize: 12, fontWeight: "600", color: colors.textFaint },
});
