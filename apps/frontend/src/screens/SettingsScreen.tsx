import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import FitbitConnectionCard from "../components/fitbit/FitbitConnectionCard";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import { getFitbitStatus, startFitbitOAuth, unlinkFitbit } from "../api/fitbit";
import type { FitbitConnectionStatus } from "../types/fitbit";

type ScreenState = "loading" | "connected" | "disconnected" | "error";

const DEFAULT_ERROR_MESSAGE = "We could not load your Fitbit connection status.";

export default function SettingsScreen() {
  const [screenState, setScreenState] = useState<ScreenState>("loading");
  const [status, setStatus] = useState<FitbitConnectionStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>(DEFAULT_ERROR_MESSAGE);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setScreenState("loading");
    setErrorMessage(DEFAULT_ERROR_MESSAGE);
    try {
      const nextStatus = await getFitbitStatus();
      setStatus(nextStatus);
      setScreenState(nextStatus.connected ? "connected" : "disconnected");
    } catch (error) {
      const message = error instanceof Error ? error.message : DEFAULT_ERROR_MESSAGE;
      setErrorMessage(message);
      setScreenState("error");
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const handleConnect = useCallback(async () => {
    setIsActionLoading(true);
    try {
      await startFitbitOAuth();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to start Fitbit OAuth right now.";
      setErrorMessage(message);
      setScreenState("error");
    } finally {
      setIsActionLoading(false);
    }
  }, []);

  const handleDisconnect = useCallback(async () => {
    setIsActionLoading(true);
    try {
      await unlinkFitbit();
      await loadStatus();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to disconnect Fitbit.";
      setErrorMessage(message);
      setScreenState("error");
    } finally {
      setIsActionLoading(false);
    }
  }, [loadStatus]);

  if (screenState === "loading") {
    return <LoadingState />;
  }

  if (screenState === "error") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Settings</Text>
        <ErrorState message={errorMessage} />
        <Pressable accessibilityRole="button" onPress={loadStatus} style={styles.retryButton}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.subtitle}>Fitbit Connection</Text>
      <FitbitConnectionCard
        isBusy={isActionLoading}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        onRefresh={loadStatus}
        status={status ?? { connected: false }}
      />
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
  subtitle: {
    color: "#374151",
    fontSize: 16,
    fontWeight: "600"
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
