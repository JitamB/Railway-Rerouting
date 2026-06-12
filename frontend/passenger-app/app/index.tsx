// Home screen: register PNR, see live delay/status, and the proactive re-route card. Skeleton.
import { View, Text } from "react-native";
import { RerouteCard } from "../components/RerouteCard";

export default function Home() {
  // TODO: PNR registration + live status; the re-route card arrives via push or poll.
  return (
    <View>
      <Text>Register your PNR to be re-routed before the delay is announced.</Text>
      <RerouteCard />
    </View>
  );
}
