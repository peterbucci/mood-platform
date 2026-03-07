import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, AppState, Pressable, StyleSheet, Text, View } from "react-native";
import type { AppStateStatus } from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import FitbitConnectionCard from "../components/fitbit/FitbitConnectionCard";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import AppCard from "../components/ui/AppCard";
import InfoText from "../components/ui/InfoText";
import SettingsSectionHeader from "../components/settings/SettingsSectionHeader";
import { getFitbitStatus, startFitbitOAuth, unlinkFitbit } from "../api/fitbit";
import type { FitbitConnectionStatus } from "../types/fitbit";
import { colors, radius, spacing, typography } from "../theme";

const DEFAULT_ERROR_MESSAGE = "We could not load your Fitbit connection status.";
const DEFAULT_APP_STATE: AppStateStatus = "active";

export default function SettingsScreen() {
  const [status, setStatus] = useState<FitbitConnectionStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>(DEFAULT_ERROR_MESSAGE);
  const [busyAction, setBusyAction] = useState<"connect" | "disconnect" | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const appStateRef = useRef<AppStateStatus>(
    typeof AppState.currentState === "string" ? AppState.currentState : DEFAULT_APP_STATE
  );
  const statusRef = useRef<FitbitConnectionStatus | null>(null);

  const loadStatus = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    const hasStatus = statusRef.current !== null;
    if (mode === "initial" && !hasStatus) {
      setIsInitialLoading(true);
    } else {
      setIsRefreshing(true);
    }

    try {
      const nextStatus = await getFitbitStatus();
      statusRef.current = nextStatus;
      setStatus(nextStatus);
      setErrorMessage("");
    } catch (error) {
      const message = error instanceof Error ? error.message : DEFAULT_ERROR_MESSAGE;
      setErrorMessage(message);
      if (mode === "initial" && !hasStatus) {
        statusRef.current = null;
        setStatus(null);
      }
    } finally {
      setIsInitialLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus("initial");
  }, [loadStatus]);

  useFocusEffect(
    useCallback(() => {
      void loadStatus(statusRef.current ? "refresh" : "initial");
    }, [loadStatus])
  );

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState) => {
      const previousState =
        typeof appStateRef.current === "string" ? appStateRef.current : DEFAULT_APP_STATE;
      const wasInBackground = /inactive|background/.test(previousState);
      appStateRef.current = nextState;
      if (wasInBackground && nextState === "active") {
        void loadStatus(statusRef.current ? "refresh" : "initial");
      }
    });
    return () => {
      if (subscription && typeof subscription.remove === "function") {
        subscription.remove();
      }
    };
  }, [loadStatus]);

  const handleConnect = useCallback(async () => {
    setBusyAction("connect");
    try {
      await startFitbitOAuth();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to start Fitbit OAuth right now.";
      setErrorMessage(message);
    } finally {
      setBusyAction(null);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    void loadStatus(statusRef.current ? "refresh" : "initial");
  }, [loadStatus]);

  const handleDisconnectConfirmed = useCallback(async () => {
    setBusyAction("disconnect");
    try {
      await unlinkFitbit();
      await loadStatus("refresh");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to disconnect Fitbit.";
      setErrorMessage(message);
    } finally {
      setBusyAction(null);
    }
  }, [loadStatus]);

  const handleDisconnect = useCallback(() => {
    Alert.alert(
      "Disconnect Fitbit?",
      "Disconnecting will stop new feature captures from Fitbit.",
      [
        { style: "cancel", text: "Cancel" },
        {
          style: "destructive",
          text: "Disconnect",
          onPress: () => {
            void handleDisconnectConfirmed();
          }
        }
      ]
    );
  }, [handleDisconnectConfirmed]);

  if (isInitialLoading && !status) {
    return <LoadingState />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.pageHeader}>
        <View style={styles.pageHeaderCopy}>
          <Text style={styles.pageTitle}>Settings</Text>
          <Text style={styles.pageSubtitle}>Manage integrations and account connections.</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          disabled={isRefreshing}
          onPress={handleRefresh}
          style={[styles.refreshButton, isRefreshing ? styles.refreshButtonDisabled : null]}
          testID="settings-refresh-button"
        >
          <Text style={styles.refreshButtonText}>{isRefreshing ? "Refreshing..." : "Refresh"}</Text>
        </Pressable>
      </View>

      <SettingsSectionHeader
        title="Fitbit Integration"
        subtitle="Connection status, permissions, and account access."
      />

      {!status && errorMessage ? (
        <AppCard style={styles.stateCard} tone="danger">
          <ErrorState message={errorMessage} />
          <AppButton label="Try Again" onPress={handleRefresh} style={styles.inlineButton} variant="neutral" />
        </AppCard>
      ) : null}

      {status ? (
        <>
          {errorMessage ? (
            <AppCard style={styles.noticeCard} tone="warning">
              <InfoText tone="warning">
                Unable to refresh your Fitbit connection. Showing your latest saved connection details.
              </InfoText>
            </AppCard>
          ) : null}

          <FitbitConnectionCard
            busyAction={busyAction}
            isRefreshing={isRefreshing}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onRefresh={handleRefresh}
            status={status}
          />
        </>
      ) : null}
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
  },
  noticeCard: {
    padding: spacing.md
  },
  pageHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  pageHeaderCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  pageSubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  pageTitle: {
    ...typography.title,
    color: colors.textPrimary
  },
  refreshButton: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  refreshButtonDisabled: {
    opacity: 0.6
  },
  refreshButtonText: {
    ...typography.helper,
    color: colors.textPrimary,
    fontWeight: "700"
  },
  stateCard: {
    gap: spacing.sm
  }
});
