// Home — register a PNR, then see live cascade risk and the proactive re-route card. The card
// normally arrives via a background push *before* the station announcement; here it is also
// fetched/refreshed in the foreground so the journey is visible on demand and on pull-to-refresh.
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { RerouteCard, type RerouteCardData } from "../components/RerouteCard";
import { getCascade, getReroute } from "../lib/api";
import { onPushReceived } from "../lib/push";
import { colors, radius, shadow, space, type } from "../lib/theme";

// Demo journey: PNR resolves to the corridor train in production; here it maps to 12301 (PNBE→BSB).
const DEMO_TRAIN = "12301";
const ROUTE = "PNBE → BSB";
const DEST = "BSB";

export default function Home() {
  const [pnr, setPnr] = useState("");
  const [tracking, setTracking] = useState<string | null>(null);
  const [data, setData] = useState<RerouteCardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (trackedPnr: string) => {
    setLoading(true);
    setError(null);
    try {
      const [cascade, reroute] = await Promise.all([getCascade(DEMO_TRAIN), getReroute(trackedPnr)]);
      const dest = cascade.stations.find((s) => s.station === DEST);
      setData({
        trainNo: cascade.train_no,
        route: ROUTE,
        riskPct: reroute.current_risk * 100,
        delayInterval: dest?.delay_interval_min ?? [0, 0],
        why: dest?.why ?? "monitoring",
        guidance: reroute.guidance,
        options: reroute.options,
        watermark: reroute.watermark,
        mode: cascade.mode,
      });
    } catch (e) {
      setError("Couldn't reach the live service. Check that the API is running, then retry.");
    } finally {
      setLoading(false);
    }
  }, []);

  // A background push means a fresh cascade — re-pull when one arrives in the foreground.
  useEffect(() => {
    if (!tracking) return;
    onPushReceived(() => void load(tracking));
  }, [tracking, load]);

  function track() {
    const value = pnr.trim();
    if (value.length < 4) {
      setError("Enter your 10-digit PNR (any value works in the demo).");
      return;
    }
    setTracking(value);
    void load(value);
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={loading && !!data}
          onRefresh={() => tracking && load(tracking)}
          tintColor={colors.brand}
        />
      }
    >
      <Text style={styles.kicker}>PROACTIVE RE-ROUTING</Text>
      <Text style={styles.title}>Stay ahead of the delay.</Text>
      <Text style={styles.subtitle}>
        Register your PNR and we'll predict cascade delays and offer feasible alternatives
        {" "}— before the platform announcement.
      </Text>

      {/* PNR registration */}
      <View style={[styles.pnrCard, shadow.card]}>
        <Text style={type.label}>YOUR PNR</Text>
        <View style={styles.pnrRow}>
          <TextInput
            style={styles.input}
            value={pnr}
            onChangeText={setPnr}
            placeholder="e.g. 8412345678"
            placeholderTextColor={colors.textFaint}
            keyboardType="number-pad"
            maxLength={10}
            returnKeyType="go"
            onSubmitEditing={track}
          />
          <TouchableOpacity style={styles.trackBtn} onPress={track} activeOpacity={0.85}>
            <Text style={styles.trackBtnText}>{tracking ? "Refresh" : "Track"}</Text>
          </TouchableOpacity>
        </View>
        {tracking && (
          <View style={styles.trackedRow}>
            <View style={styles.liveDot} />
            <Text style={styles.trackedText}>Tracking PNR ••••{tracking.slice(-4)} on {DEMO_TRAIN}</Text>
          </View>
        )}
      </View>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {loading && !data && (
        <View style={styles.loadingBox}>
          <ActivityIndicator color={colors.brand} />
          <Text style={styles.loadingText}>Reading the live cascade…</Text>
        </View>
      )}

      {data && <RerouteCard data={data} />}

      {!tracking && !loading && (
        <View style={styles.empty}>
          <Text style={styles.emptyEmoji}>🚆</Text>
          <Text style={styles.emptyText}>
            No journey tracked yet. Add a PNR above to see live risk and alternatives.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space(5), paddingBottom: space(12), gap: space(4) as number },
  kicker: { ...type.label, color: colors.brandSoft },
  title: { ...type.display, marginTop: space(1) },
  subtitle: { ...type.body, marginTop: space(1) },
  pnrCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space(4),
    marginTop: space(2),
  },
  pnrRow: { flexDirection: "row", gap: space(2) as number, marginTop: space(2) },
  input: {
    flex: 1,
    backgroundColor: colors.surfaceAlt,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.lg,
    paddingHorizontal: space(4),
    paddingVertical: space(3),
    fontSize: 16,
    fontWeight: "700",
    color: colors.text,
    letterSpacing: 1,
  },
  trackBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.lg,
    paddingHorizontal: space(5),
    justifyContent: "center",
  },
  trackBtnText: { color: colors.white, fontWeight: "800", fontSize: 15 },
  trackedRow: { flexDirection: "row", alignItems: "center", gap: space(2) as number, marginTop: space(3) },
  liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.green },
  trackedText: { fontSize: 13, fontWeight: "700", color: colors.textMute },
  errorBox: { backgroundColor: colors.redBg, borderRadius: radius.lg, padding: space(4) },
  errorText: { color: colors.red, fontWeight: "700", fontSize: 14 },
  loadingBox: { alignItems: "center", padding: space(8), gap: space(3) as number },
  loadingText: { color: colors.textMute, fontWeight: "600" },
  empty: { alignItems: "center", padding: space(8), gap: space(3) as number },
  emptyEmoji: { fontSize: 40 },
  emptyText: { textAlign: "center", color: colors.textFaint, fontWeight: "600", maxWidth: 280 },
});
