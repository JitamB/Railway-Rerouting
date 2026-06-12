// "My Queries" screen: past helpline queries and their status. Skeleton.
import { View, Text } from "react-native";
import { QueryHistory } from "../components/QueryHistory";

export default function Queries() {
  return (
    <View>
      <Text>Track your past questions and complaints.</Text>
      <QueryHistory />
    </View>
  );
}
