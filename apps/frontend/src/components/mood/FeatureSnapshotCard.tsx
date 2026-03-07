import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";

type FeatureSnapshotCardProps = {
  capturedAt?: string | null;
  featureId: string;
  helperText: string;
  sourceLabel?: string | null;
};

export default function FeatureSnapshotCard({
  capturedAt,
  featureId,
  helperText,
  sourceLabel
}: FeatureSnapshotCardProps) {
  return (
    <AppCard tone="info" style={styles.card}>
      <Text style={styles.title}>Feature Snapshot</Text>
      {capturedAt ? <Text style={styles.captureText}>{capturedAt}</Text> : null}
      {sourceLabel ? <Text style={styles.sourceText}>Source: {sourceLabel}</Text> : null}
      <Text style={styles.helperText}>{helperText}</Text>
      <View style={styles.idRow}>
        <Text style={styles.idLabel}>ID</Text>
        <Text style={styles.idValue}>{featureId}</Text>
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  captureText: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  card: {
    gap: spacing.xs
  },
  helperText: {
    ...typography.body,
    color: colors.textSecondary
  },
  idLabel: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  idRow: {
    gap: spacing.xxs
  },
  idValue: {
    ...typography.helper,
    color: colors.textSecondary
  },
  sourceText: {
    ...typography.helper,
    color: colors.infoText
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
