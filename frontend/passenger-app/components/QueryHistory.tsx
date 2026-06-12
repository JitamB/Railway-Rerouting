// Past queries list with status badges (open / in_progress / resolved / rejected). Skeleton.
// Fetches GET /queries?passenger_id=...; tap a row to see GET /queries/{case_id} history.
import { View } from "react-native";

export function QueryHistory() {
  // TODO: fetch and render the passenger's cases (newest first) with status + department.
  return <View accessibilityLabel="query-history" />;
}
