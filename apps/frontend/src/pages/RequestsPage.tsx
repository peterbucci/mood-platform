import { useCallback } from "react";
import { useIsFocused, useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import CreateRequestCard from "../components/requests/CreateRequestCard";
import PendingCountCard from "../components/requests/PendingCountCard";
import RequestList from "../components/requests/RequestList";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import { DEFAULT_REQUEST_POLL_INTERVAL_MS, useRequestPolling } from "../hooks/useRequestPolling";
import type { RootStackParamList } from "../router/AppRouter";

export default function RequestsPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const isFocused = useIsFocused();
  const {
    cancelErrorById,
    cancelPendingRequest,
    cancelingById,
    requests,
    pendingCount,
    errorMessage,
    isInitialLoading,
    isPolling,
    isRefreshing,
    refresh
  } = useRequestPolling({
    enabled: isFocused,
    pollIntervalMs: DEFAULT_REQUEST_POLL_INTERVAL_MS
  });

  const handleOpenFeature = useCallback(
    (featureId: string) => {
      navigation.navigate("FeatureDetail", { id: featureId });
    },
    [navigation]
  );

  const handleCancelRequest = useCallback(
    async (requestId: string) => {
      await cancelPendingRequest(requestId);
    },
    [cancelPendingRequest]
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Requests</Text>
      <Text style={styles.description}>Track feature capture requests and pending queue state.</Text>
      <PendingCountCard pendingCount={pendingCount} />
      {isPolling ? (
        <Text style={styles.pollingText}>Auto-refreshing pending requests every few seconds...</Text>
      ) : null}
      <Pressable
        accessibilityRole="button"
        disabled={isInitialLoading || isRefreshing}
        onPress={refresh}
        style={[styles.refreshButton, isInitialLoading || isRefreshing ? styles.buttonDisabled : null]}
      >
        <Text style={styles.refreshButtonText}>{isRefreshing ? "Refreshing..." : "Refresh"}</Text>
      </Pressable>
      <CreateRequestCard onCreated={refresh} />

      {isInitialLoading ? <LoadingState message="Loading requests..." /> : null}
      {!isInitialLoading && errorMessage && requests.length === 0 ? (
        <View style={styles.errorContainer}>
          <ErrorState message={errorMessage} />
          <Pressable accessibilityRole="button" onPress={refresh} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </Pressable>
        </View>
      ) : null}
      {!isInitialLoading && !errorMessage && requests.length === 0 ? (
        <EmptyState message="No feature requests yet. Trigger a capture to get started." />
      ) : null}
      {requests.length > 0 ? (
        <RequestList
          cancelErrorById={cancelErrorById}
          cancelingById={cancelingById}
          onPressCancel={handleCancelRequest}
          onPressFeature={handleOpenFeature}
          requests={requests}
        />
      ) : null}
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
  pollingText: {
    color: "#92400e",
    fontSize: 13,
    fontWeight: "600"
  },
  refreshButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  buttonDisabled: {
    opacity: 0.65
  },
  refreshButtonText: {
    color: "#ffffff",
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
