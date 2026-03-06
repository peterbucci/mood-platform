import { StyleSheet, Text, View } from "react-native";

export default function FeaturesPage() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Features</Text>
      <Text style={styles.description}>
        This page will list generated feature snapshots for the current user.
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
