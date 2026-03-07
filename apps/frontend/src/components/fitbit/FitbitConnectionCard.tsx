import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { FitbitConnectionStatus } from "../../types/fitbit";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type FitbitConnectionCardProps = {
  status: FitbitConnectionStatus;
  isBusy?: boolean;
  onConnect: () => void;
  onDisconnect?: () => void;
};

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "N/A";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export default function FitbitConnectionCard({
  status,
  isBusy = false,
  onConnect,
  onDisconnect
}: FitbitConnectionCardProps) {
  if (!status.connected) {
    return (
      <AppCard style={styles.card} tone="warning">
        <Text style={styles.title}>Fitbit not connected</Text>
        <InfoText tone="helper">
          Feature requests may not be fulfilled until your Fitbit account is connected.
        </InfoText>
        <AppButton
          onPress={onConnect}
          isLoading={isBusy}
          label="Connect Fitbit"
        />
      </AppCard>
    );
  }

  return (
    <AppCard style={styles.card} tone="success">
      <Text style={styles.title}>Fitbit connected</Text>
      <InfoText tone="helper">Your account is ready for feature fulfillment.</InfoText>
      <View style={styles.metaContainer}>
        <Text style={styles.metaRow}>Status: Connected</Text>
        <Text style={styles.metaRow}>Fitbit user id: {status.fitbitUserId ?? "N/A"}</Text>
        <Text style={styles.metaRow}>Last sync: {formatDate(status.lastSyncAt)}</Text>
        <Text style={styles.metaRow}>Expires: {formatDate(status.expiresAt)}</Text>
        <Text style={styles.metaRow}>
          Scopes: {status.scopes && status.scopes.length > 0 ? status.scopes.join(", ") : "N/A"}
        </Text>
      </View>
      <View style={styles.actionRow}>
        <AppButton label="Reconnect Fitbit" onPress={onConnect} disabled={isBusy} variant="neutral" />
        {onDisconnect ? (
          <AppButton label="Disconnect Fitbit" onPress={onDisconnect} disabled={isBusy} variant="danger" />
        ) : null}
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  },
  metaContainer: {
    backgroundColor: colors.surface,
    borderColor: colors.successBorder,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xxs,
    padding: spacing.md
  },
  metaRow: {
    ...typography.helper,
    color: colors.textSecondary
  },
  actionRow: {
    flexDirection: "column",
    gap: spacing.sm
  }
});
