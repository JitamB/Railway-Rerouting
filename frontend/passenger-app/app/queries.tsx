// "My Queries" screen: past helpline queries and their status.
import { StyleSheet, Text, View } from "react-native";
import { QueryHistory } from "../components/QueryHistory";
import { colors, space, type } from "../lib/theme";

export default function Queries() {
  return (
    <View style={styles.screen}>
      <View style={styles.head}>
        <Text style={styles.title}>My Queries</Text>
        <Text style={styles.subtitle}>Track your past questions and complaints.</Text>
      </View>
      <QueryHistory />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  head: { paddingHorizontal: space(5), paddingTop: space(4), paddingBottom: space(2) },
  title: { ...type.h1 },
  subtitle: { ...type.body, marginTop: space(1) },
});
