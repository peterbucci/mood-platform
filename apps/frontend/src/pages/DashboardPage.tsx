import { StyleSheet, Text, View } from "react-native";

export default function DashboardPage() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>
      <Text style={styles.description}>
        High-level overview of Fitbit connection health, request queue, and latest generated
        features.
      </Text>
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
