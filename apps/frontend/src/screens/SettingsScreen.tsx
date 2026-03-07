import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, StyleSheet, View } from "react-native";
import type { AppStateStatus } from "react-native";
import { useFocusEffect, useIsFocused } from "@react-navigation/native";

import FitbitConnectionCard from "../components/fitbit/FitbitConnectionCard";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import SectionHeader from "../components/ui/SectionHeader";
import { getFitbitStatus, startFitbitOAuth, unlinkFitbit } from "../api/fitbit";
import { useAppRefreshListener } from "../hooks/useAppRefresh";
import type { FitbitConnectionStatus } from "../types/fitbit";
import { spacing } from "../theme";

type ScreenState = "loading" | "connected" | "disconnected" | "error";

const DEFAULT_ERROR_MESSAGE = "We could not load your Fitbit connection status.";
const DEFAULT_APP_STATE: AppStateStatus = "active";

export default function SettingsScreen() {
  const isFocused = useIsFocused();
  const [screenState, setScreenState] = useState<ScreenState>("loading");
  const [status, setStatus] = useState<FitbitConnectionStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>(DEFAULT_ERROR_MESSAGE);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const appStateRef = useRef<AppStateStatus>(
    typeof AppState.currentState === "string" ? AppState.currentState : DEFAULT_APP_STATE
  );

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

  useFocusEffect(
    useCallback(() => {
      void loadStatus();
    }, [loadStatus])
  );

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState) => {
      const previousState =
        typeof appStateRef.current === "string" ? appStateRef.current : DEFAULT_APP_STATE;
      const wasInBackground = /inactive|background/.test(previousState);
      appStateRef.current = nextState;
      if (wasInBackground && nextState === "active") {
        void loadStatus();
      }
    });
    return () => {
      if (subscription && typeof subscription.remove === "function") {
        subscription.remove();
      }
    };
  }, [loadStatus]);

  useAppRefreshListener(() => {
    if (!isFocused) {
      return;
    }
    void loadStatus();
  });

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
        <SectionHeader title="Settings" />
        <ErrorState message={errorMessage} />
        <AppButton label="Try Again" onPress={loadStatus} style={styles.inlineButton} variant="neutral" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionHeader title="Settings" subtitle="Fitbit Connection" />
      <FitbitConnectionCard
        isBusy={isActionLoading}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        status={status ?? { connected: false }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 128
  }
});
