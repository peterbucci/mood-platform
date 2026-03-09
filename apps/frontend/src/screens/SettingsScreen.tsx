import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, AppState, Pressable, StyleSheet, Text, View } from "react-native";
import type { AppStateStatus } from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import FitbitConnectionCard from "../components/fitbit/FitbitConnectionCard";
import FitbitConfigurationCard, {
  type FitbitConfigurationField,
  type FitbitConfigurationFieldErrors,
  type FitbitConfigurationFormValues
} from "../components/settings/FitbitConfigurationCard";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import AppCard from "../components/ui/AppCard";
import InfoText from "../components/ui/InfoText";
import SettingsSectionHeader from "../components/settings/SettingsSectionHeader";
import { isApiError } from "../api/errors";
import {
  getFitbitSettings,
  getFitbitStatus,
  startFitbitOAuth,
  unlinkFitbit,
  updateFitbitSettings
} from "../api/fitbit";
import type { FitbitConnectionStatus } from "../types/fitbit";
import { colors, radius, spacing, typography } from "../theme";

const DEFAULT_CONNECTION_ERROR_MESSAGE = "We could not load your Fitbit connection status.";
const DEFAULT_CONFIG_ERROR_MESSAGE = "We could not load your Fitbit integration settings.";
const DEFAULT_APP_STATE: AppStateStatus = "active";
const EMPTY_CONFIG_FORM: FitbitConfigurationFormValues = {
  clientId: "",
  clientSecret: "",
  redirectUri: "",
  scope: "",
  subscriberId: "",
  webhookSecret: ""
};

type SecretFieldName = "clientSecret" | "webhookSecret";

export default function SettingsScreen() {
  const [status, setStatus] = useState<FitbitConnectionStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>(DEFAULT_CONNECTION_ERROR_MESSAGE);
  const [busyAction, setBusyAction] = useState<"connect" | "disconnect" | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [configFormValues, setConfigFormValues] = useState<FitbitConfigurationFormValues>(EMPTY_CONFIG_FORM);
  const [configFieldErrors, setConfigFieldErrors] = useState<FitbitConfigurationFieldErrors>({});
  const [clientSecretMasked, setClientSecretMasked] = useState<string | null>(null);
  const [configLoadErrorMessage, setConfigLoadErrorMessage] = useState<string | null>(null);
  const [configSaveErrorMessage, setConfigSaveErrorMessage] = useState<string | null>(null);
  const [configSuccessMessage, setConfigSuccessMessage] = useState<string | null>(null);
  const [hasStoredClientSecret, setHasStoredClientSecret] = useState(false);
  const [hasStoredWebhookSecret, setHasStoredWebhookSecret] = useState(false);
  const [isConfigLoading, setIsConfigLoading] = useState(true);
  const [isSavingConfiguration, setIsSavingConfiguration] = useState(false);
  const [secretEdited, setSecretEdited] = useState<Record<SecretFieldName, boolean>>({
    clientSecret: false,
    webhookSecret: false
  });
  const [webhookSecretMasked, setWebhookSecretMasked] = useState<string | null>(null);
  const appStateRef = useRef<AppStateStatus>(
    typeof AppState.currentState === "string" ? AppState.currentState : DEFAULT_APP_STATE
  );
  const statusRef = useRef<FitbitConnectionStatus | null>(null);

  const applyLoadedConfiguration = useCallback((payload: Awaited<ReturnType<typeof getFitbitSettings>>) => {
    setConfigFormValues({
      clientId: payload.clientId,
      clientSecret: payload.clientSecretMasked ?? "",
      redirectUri: payload.redirectUri,
      scope: payload.scope,
      subscriberId: payload.subscriberId,
      webhookSecret: payload.webhookSecretMasked ?? ""
    });
    setClientSecretMasked(payload.clientSecretMasked ?? null);
    setWebhookSecretMasked(payload.webhookSecretMasked ?? null);
    setHasStoredClientSecret(Boolean(payload.hasClientSecret));
    setHasStoredWebhookSecret(Boolean(payload.hasWebhookSecret));
    setSecretEdited({
      clientSecret: false,
      webhookSecret: false
    });
    setConfigFieldErrors({});
  }, []);

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
      const message = error instanceof Error ? error.message : DEFAULT_CONNECTION_ERROR_MESSAGE;
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

  const loadConfiguration = useCallback(async () => {
    setIsConfigLoading(true);
    try {
      const payload = await getFitbitSettings();
      applyLoadedConfiguration(payload);
      setConfigLoadErrorMessage(null);
      setConfigSaveErrorMessage(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : DEFAULT_CONFIG_ERROR_MESSAGE;
      setConfigLoadErrorMessage(message);
    } finally {
      setIsConfigLoading(false);
    }
  }, [applyLoadedConfiguration]);

  useEffect(() => {
    void loadStatus("initial");
    void loadConfiguration();
  }, [loadConfiguration, loadStatus]);

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
    void loadConfiguration();
  }, [loadConfiguration, loadStatus]);

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

  const handleChangeConfigField = useCallback((field: FitbitConfigurationField, value: string) => {
    setConfigFormValues((current) => ({
      ...current,
      [field]: value
    }));
    setConfigFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
    setConfigSaveErrorMessage(null);
    setConfigSuccessMessage(null);
  }, []);

  const handleFocusSecretField = useCallback(
    (field: SecretFieldName) => {
      setSecretEdited((current) => {
        if (current[field]) {
          return current;
        }
        return {
          ...current,
          [field]: true
        };
      });
      setConfigFormValues((current) => {
        const maskedValue = field === "clientSecret" ? clientSecretMasked : webhookSecretMasked;
        if (!maskedValue || current[field] !== maskedValue) {
          return current;
        }
        return {
          ...current,
          [field]: ""
        };
      });
      setConfigSaveErrorMessage(null);
      setConfigSuccessMessage(null);
    },
    [clientSecretMasked, webhookSecretMasked]
  );

  const handleSaveConfiguration = useCallback(async () => {
    const nextErrors: FitbitConfigurationFieldErrors = {};
    const clientId = configFormValues.clientId.trim();
    const redirectUri = configFormValues.redirectUri.trim();
    const scope = configFormValues.scope.trim();
    const subscriberId = configFormValues.subscriberId.trim();
    const clientSecret =
      secretEdited.clientSecret || !hasStoredClientSecret
        ? configFormValues.clientSecret.trim()
        : undefined;
    const webhookSecret = secretEdited.webhookSecret ? configFormValues.webhookSecret.trim() : undefined;

    if (!clientId) {
      nextErrors.clientId = "Client ID is required.";
    }
    if (!redirectUri) {
      nextErrors.redirectUri = "Redirect URI is required.";
    }
    if ((secretEdited.clientSecret || !hasStoredClientSecret) && !clientSecret) {
      nextErrors.clientSecret = "Client Secret is required.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setConfigFieldErrors(nextErrors);
      setConfigSaveErrorMessage(null);
      setConfigSuccessMessage(null);
      return;
    }

    setIsSavingConfiguration(true);
    setConfigSaveErrorMessage(null);
    setConfigSuccessMessage(null);

    try {
      const saved = await updateFitbitSettings({
        clientId,
        clientSecret,
        redirectUri,
        scope,
        subscriberId,
        webhookSecret
      });
      applyLoadedConfiguration(saved);
      setConfigLoadErrorMessage(null);
      setConfigSaveErrorMessage(null);
      setConfigSuccessMessage("Fitbit configuration saved.");
    } catch (error) {
      if (isApiError(error)) {
        const detail = error.details as { detail?: { errors?: Record<string, string> } } | undefined;
        const nestedErrors = detail?.detail?.errors;
        if (nestedErrors && typeof nestedErrors === "object") {
          const mappedErrors: FitbitConfigurationFieldErrors = {};
          if (typeof nestedErrors.clientId === "string") {
            mappedErrors.clientId = nestedErrors.clientId;
          }
          if (typeof nestedErrors.clientSecret === "string") {
            mappedErrors.clientSecret = nestedErrors.clientSecret;
          }
          if (typeof nestedErrors.redirectUri === "string") {
            mappedErrors.redirectUri = nestedErrors.redirectUri;
          }
          setConfigFieldErrors(mappedErrors);
        }
      }

      const message = error instanceof Error ? error.message : "Unable to save Fitbit settings.";
      setConfigSaveErrorMessage(message);
      setConfigSuccessMessage(null);
    } finally {
      setIsSavingConfiguration(false);
    }
  }, [
    applyLoadedConfiguration,
    configFormValues.clientId,
    configFormValues.clientSecret,
    configFormValues.redirectUri,
    configFormValues.scope,
    configFormValues.subscriberId,
    configFormValues.webhookSecret,
    hasStoredClientSecret,
    secretEdited.clientSecret,
    secretEdited.webhookSecret
  ]);

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
          disabled={isRefreshing || isConfigLoading || isSavingConfiguration}
          onPress={handleRefresh}
          style={[
            styles.refreshButton,
            isRefreshing || isConfigLoading || isSavingConfiguration ? styles.refreshButtonDisabled : null
          ]}
          testID="settings-refresh-button"
        >
          <Text style={styles.refreshButtonText}>
            {isRefreshing || isConfigLoading ? "Refreshing..." : "Refresh"}
          </Text>
        </Pressable>
      </View>

      <SettingsSectionHeader
        title="Fitbit Integration"
        subtitle="Connection status, OAuth credentials, and webhook configuration."
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

      <FitbitConfigurationCard
        clientSecretHint={clientSecretMasked}
        fieldErrors={configFieldErrors}
        formValues={configFormValues}
        isLoading={isConfigLoading}
        isSaving={isSavingConfiguration}
        loadErrorMessage={configLoadErrorMessage}
        onChangeField={handleChangeConfigField}
        onFocusSecretField={handleFocusSecretField}
        onSave={() => void handleSaveConfiguration()}
        saveErrorMessage={configSaveErrorMessage}
        successMessage={configSuccessMessage}
        webhookSecretHint={webhookSecretMasked}
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
