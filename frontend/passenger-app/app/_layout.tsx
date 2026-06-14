// Root navigation (Expo Router tabs): Home · Helpline · My Queries.
// Branded header + icon tab bar; registers background push once on mount.
import { useEffect } from "react";
import { StatusBar } from "react-native";
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "../lib/theme";
import { registerPush } from "../lib/push";

export default function RootLayout() {
  useEffect(() => {
    registerPush();
  }, []);

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor={colors.brand} />
      <Tabs
        screenOptions={{
          headerStyle: { backgroundColor: colors.brand },
          headerTintColor: colors.white,
          headerTitleStyle: { fontWeight: "800", letterSpacing: 0.3 },
          headerTitle: "CascadeGuard",
          tabBarActiveTintColor: colors.brandSoft,
          tabBarInactiveTintColor: colors.textFaint,
          tabBarStyle: {
            backgroundColor: colors.surface,
            borderTopColor: colors.border,
            height: 62,
            paddingTop: 6,
            paddingBottom: 8,
          },
          tabBarLabelStyle: { fontSize: 11, fontWeight: "700" },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Home",
            tabBarIcon: ({ color, size }) => <Ionicons name="train" size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="helpline"
          options={{
            title: "Helpline",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="chatbubbles" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="queries"
          options={{
            title: "My Queries",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="document-text" size={size} color={color} />
            ),
          }}
        />
      </Tabs>
    </>
  );
}
