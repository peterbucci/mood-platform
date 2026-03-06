import { StyleSheet, Text, View } from "react-native";

import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";

type RequestsViewState = "loading" | "empty" | "error" | "ready";

export default function RequestsPage() {
  // Placeholder state handling to demonstrate shared UI states.
  const viewState = getRequestsViewState();

  if (viewState === "loading") {
    return <LoadingState />;
  }

  if (viewState === "error") {
    return <ErrorState message="Failed to load request status." />;
  }

  if (viewState === "empty") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Requests</Text>
        <EmptyState message="No feature requests yet. Trigger a capture to get started." />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Requests</Text>
      <Text style={styles.description}>Request list placeholder.</Text>
    </View>
  );
}

function getRequestsViewState(): RequestsViewState {
  return "empty";
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
