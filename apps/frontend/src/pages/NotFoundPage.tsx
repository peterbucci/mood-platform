import { StyleSheet, Text, View } from "react-native";

import ErrorState from "../components/states/ErrorState";

export default function NotFoundPage() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Page Not Found</Text>
      <ErrorState message="We could not find the route you requested." />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 10
  },
  title: {
    color: "#111827",
    fontSize: 24,
    fontWeight: "700"
  }
});
