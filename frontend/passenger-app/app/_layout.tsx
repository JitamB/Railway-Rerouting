// Root navigation (Expo Router tabs): Home · Helpline · My Queries.
// Registers push handling once on mount. Skeleton.
import { useEffect } from "react";
import { Tabs } from "expo-router";
import { registerPush } from "../lib/push";

export default function RootLayout() {
  useEffect(() => {
    registerPush();
  }, []);

  return (
    <Tabs screenOptions={{ headerTitle: "CascadeGuard" }}>
      <Tabs.Screen name="index" options={{ title: "Home" }} />
      <Tabs.Screen name="helpline" options={{ title: "Helpline" }} />
      <Tabs.Screen name="queries" options={{ title: "My Queries" }} />
    </Tabs>
  );
}
