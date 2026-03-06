import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getPendingRequestCount, getRequests } from "../api/requests";
import CreateRequestCard from "../components/requests/CreateRequestCard";
import RequestRow from "../components/requests/RequestRow";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import type { FeatureRequestRecord } from "../types/requests";

type RequestsViewState = "loading" | "error" | "ready";

export default function RequestsPage() {
  const [viewState, setViewState] = useState<RequestsViewState>("loading");
  const [requests, setRequests] = useState<FeatureRequestRecord[]>([]);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadRequests = useCallback(async () => {
    setErrorMessage(null);
    try {
      const [items, nextPendingCount] = await Promise.all([getRequests(), getPendingRequestCount()]);
      setRequests(items);
      setPendingCount(nextPendingCount);
      setViewState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load requests.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, []);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Requests</Text>
      <Text style={styles.description}>Track feature capture requests and pending queue state.</Text>
      <Text style={styles.pendingCount}>Pending requests: {pendingCount}</Text>
      <CreateRequestCard onCreated={loadRequests} />

      {viewState === "loading" ? <LoadingState message="Loading requests..." /> : null}
      {viewState === "error" ? (
        <View style={styles.errorContainer}>
          <ErrorState message={errorMessage ?? "Failed to load requests."} />
          <Pressable accessibilityRole="button" onPress={loadRequests} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </Pressable>
        </View>
      ) : null}
      {viewState === "ready" && requests.length === 0 ? (
        <EmptyState message="No feature requests yet. Trigger a capture to get started." />
      ) : null}
      {viewState === "ready" && requests.length > 0
        ? requests.map((request) => <RequestRow key={request.id} request={request} />)
        : null}
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
  },
  description: {
    color: "#4b5563",
    fontSize: 16
  },
  pendingCount: {
    color: "#1f2937",
    fontSize: 14,
    fontWeight: "600"
  },
  errorContainer: {
    gap: 8
  },
  retryButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  retryButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
  }
});
