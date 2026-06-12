// Helpline screen: chat with the support agent by text or regional-language speech. Skeleton.
import { View, Text } from "react-native";
import { HelplineChat } from "../components/HelplineChat";

export default function Helpline() {
  return (
    <View>
      <Text>Ask a question or raise a complaint — type or speak in your language.</Text>
      <HelplineChat />
    </View>
  );
}
