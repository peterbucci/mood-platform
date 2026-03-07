import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { FitbitConnectionStatus } from "../../types/fitbit";
import {
  formatFitbitExpirationHint,
  formatFitbitRelativeTime,
  formatFitbitTimestamp,
  getFitbitConnectionPresentation
} from "../../utils/fitbitConnectionFormatting";
import FitbitActionButtons from "../settings/FitbitActionButtons";
import FitbitPermissionsSection from "../settings/FitbitPermissionsSection";
import FitbitStatusIndicator from "../settings/FitbitStatusIndicator";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type FitbitConnectionCardProps = {
  busyAction?: "connect" | "disconnect" | null;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  status: FitbitConnectionStatus;
  onConnect: () => void;
  onDisconnect?: () => void;
};

type DetailTileProps = {
  hint?: string | null;
  label: string;
  value: string;
};

function DetailTile({ hint, label, value }: DetailTileProps) {
  return (
    <View style={styles.detailTile}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
      {hint ? <Text style={styles.detailHint}>{hint}</Text> : null}
    </View>
  );
}

export default function FitbitConnectionCard({
  busyAction = null,
  isRefreshing = false,
  onRefresh,
  status,
  onConnect,
  onDisconnect
}: FitbitConnectionCardProps) {
  const nowMs = Date.now();
  const presentation = getFitbitConnectionPresentation(status, nowMs);
  const lastSyncValue = status.lastSyncAt ? formatFitbitTimestamp(status.lastSyncAt, nowMs) : "No sync yet";
  const lastSyncHint = status.lastSyncAt ? formatFitbitRelativeTime(status.lastSyncAt, nowMs) : "Waiting for your first sync";
  const expiresValue = status.expiresAt ? formatFitbitTimestamp(status.expiresAt, nowMs) : "Unavailable";
  const expiresHint = status.expiresAt ? formatFitbitExpirationHint(status.expiresAt, nowMs) : "Expiration unavailable";

  return (
    <AppCard style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>{presentation.title}</Text>
          <InfoText tone="helper">{presentation.description}</InfoText>
        </View>
        <FitbitStatusIndicator label={presentation.statusLabel} tone={presentation.tone} />
      </View>

      {status.connected ? (
        <>
          <View style={styles.detailGrid}>
            <DetailTile hint={lastSyncHint} label="Last sync" value={lastSyncValue} />
            <DetailTile hint={expiresHint} label="Connection expires" value={expiresValue} />
          </View>

          {status.fitbitUserId ? (
            <View style={styles.referenceBlock}>
              <Text style={styles.referenceLabel}>Fitbit user ID</Text>
              <Text style={styles.referenceValue}>{status.fitbitUserId}</Text>
            </View>
          ) : null}

          {status.scopes && status.scopes.length > 0 ? (
            <FitbitPermissionsSection scopes={status.scopes} />
          ) : null}
        </>
      ) : null}

      <FitbitActionButtons
        busyAction={busyAction}
        connected={status.connected}
        isRefreshing={isRefreshing}
        onConnect={onConnect}
        onDisconnect={onDisconnect}
        onRefresh={onRefresh}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  detailGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    justifyContent: "space-between"
  },
  detailHint: {
    ...typography.helper,
    color: colors.textMuted
  },
  detailLabel: {
    ...typography.helper,
    color: colors.textSecondary,
    fontWeight: "700",
    textTransform: "uppercase"
  },
  detailTile: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xxs,
    minHeight: 92,
    padding: spacing.md,
    width: "48%"
  },
  detailValue: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  headerCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  headerRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  referenceBlock: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xxs,
    padding: spacing.md
  },
  referenceLabel: {
    ...typography.helper,
    color: colors.textSecondary
  },
  referenceValue: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  }
});
