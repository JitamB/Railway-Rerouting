// The re-route card: current delay, probability, feasible alternatives, and the "why".
// Safety-critical fields (train no., platform, time) come from structured data, not LLM prose.
// Seat reality (AVL/WL/Tatkal/FULL) and the staleness watermark are always shown. Skeleton.
import { View } from "react-native";

export function RerouteCard() {
  // TODO: render risk %, conformal interval, 1-3 alternatives, why-line, seats, data-age.
  return <View accessibilityLabel="reroute-card" />;
}
