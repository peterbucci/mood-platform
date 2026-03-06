import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../router/AppRouter";

type FeatureDetailPageProps = NativeStackScreenProps<RootStackParamList, "FeatureDetail">;

export default function FeatureDetailPage({ route }: FeatureDetailPageProps) {
  const { id } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Feature Detail</Text>
      <Text style={styles.description}>Placeholder for feature id: {id}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8
  },
  title: {
    color: "#111827",
    fontSize: 24,
    fontWeight: "700"
  },
  description: {
    color: "#4b5563",
    fontSize: 16
  }
});
