import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { FeatureKeyMetric } from "../../utils/featureFormatting";
import AppCard from "../ui/AppCard";

type FeatureKeyMetricsCardProps = {
  metrics: FeatureKeyMetric[];
};

export default function FeatureKeyMetricsCard({ metrics }: FeatureKeyMetricsCardProps) {
  return (
    <AppCard style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Key Metrics</Text>
        <Text style={styles.subtitle}>The most useful signals from this snapshot.</Text>
      </View>

      {metrics.length > 0 ? (
        <View style={styles.grid}>
          {metrics.map((metric) => (
            <View key={metric.key} style={styles.metricTile}>
              <Text style={styles.metricLabel}>{metric.label}</Text>
              <Text style={styles.metricValue}>{metric.value}</Text>
            </View>
          ))}
        </View>
      ) : (
        <Text style={styles.emptyText}>No user-friendly summary metrics are available for this snapshot yet.</Text>
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  header: {
    gap: spacing.xxs
  },
  metricLabel: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  metricTile: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xs,
    minHeight: 82,
    padding: spacing.md,
    width: "48%"
  },
  metricValue: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
