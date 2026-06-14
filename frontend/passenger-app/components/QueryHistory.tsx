// Past helpline queries with status badges (open / in_progress / resolved / rejected).
// Fetches GET /queries?passenger_id=…; newest first. The grievance service is the Stage-9 track,
// so an empty/not-yet-implemented response renders a friendly empty state rather than an error.
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { getQueries, type QuerySummary } from "../lib/api";
import { colors, radius, shadow, space, type } from "../lib/theme";

const PASSENGER_ID = "demo-passenger";

const STATUS_TONE: Record<string, { fg: string; bg: string }> = {
  open: { fg: colors.amber, bg: colors.amberBg },
  in_progress: { fg: colors.brandSoft, bg: colors.brandTint },
  resolved: { fg: colors.green, bg: colors.greenBg },
  rejected: { fg: colors.red, bg: colors.redBg },
};

export function QueryHistory() {
  const [items, setItems] = useState<QuerySummary[] | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await getQueries(PASSENGER_ID));
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.brand} />
      </View>
    );
  }

  if (!items || items.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyEmoji}>📋</Text>
        <Text style={styles.emptyText}>No queries yet. Raise one from the Helpline tab and it'll show here.</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(q) => q.case_id}
      contentContainerStyle={styles.list}
      renderItem={({ item }) => {
        const tone = STATUS_TONE[item.status] ?? STATUS_TONE.open;
        return (
          <View style={[styles.card, shadow.card]}>
            <View style={styles.cardHeader}>
              <Text style={styles.caseId}>Case {item.case_id}</Text>
              <View style={[styles.badge, { backgroundColor: tone.bg }]}>
                <Text style={[styles.badgeText, { color: tone.fg }]}>{item.status.replace("_", " ")}</Text>
              </View>
            </View>
            <Text style={styles.summary} numberOfLines={2}>{item.summary}</Text>
            <View style={styles.metaRow}>
              <Text style={styles.metaTag}>{item.category}</Text>
              <Text style={styles.metaDot}>·</Text>
              <Text style={styles.metaDept}>{item.department}</Text>
            </View>
          </View>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: space(8), gap: space(3) as number },
  emptyEmoji: { fontSize: 40 },
  emptyText: { textAlign: "center", color: colors.textFaint, fontWeight: "600", maxWidth: 280 },
  list: { padding: space(4), gap: space(3) as number },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space(4),
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  caseId: { fontSize: 13, fontWeight: "800", color: colors.textMute, letterSpacing: 0.3 },
  badge: { paddingHorizontal: space(2.5), paddingVertical: 2, borderRadius: radius.pill },
  badgeText: { fontSize: 11, fontWeight: "800", textTransform: "capitalize" },
  summary: { ...type.h2, fontSize: 15, marginTop: space(2), marginBottom: space(2.5) },
  metaRow: { flexDirection: "row", alignItems: "center", gap: space(2) as number },
  metaTag: { fontSize: 12, fontWeight: "800", color: colors.brandSoft, textTransform: "uppercase", letterSpacing: 0.3 },
  metaDot: { color: colors.textFaint },
  metaDept: { fontSize: 12, fontWeight: "700", color: colors.textFaint },
});
