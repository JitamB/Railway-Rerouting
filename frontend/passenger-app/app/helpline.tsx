// Helpline screen: chat with the support agent by text or regional-language speech.
import { StyleSheet, Text, View } from "react-native";
import { HelplineChat } from "../components/HelplineChat";
import { colors, space, type } from "../lib/theme";

export default function Helpline() {
  return (
    <View style={styles.screen}>
      <View style={styles.head}>
        <Text style={styles.title}>Helpline</Text>
        <Text style={styles.subtitle}>Ask a question or raise a complaint — type or speak in your language.</Text>
      </View>
      <HelplineChat />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  head: { paddingHorizontal: space(5), paddingTop: space(4), paddingBottom: space(2) },
  title: { ...type.h1 },
  subtitle: { ...type.body, marginTop: space(1) },
});
