import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";

type InsightCardProps = {
  insights: string[];
};

export default function InsightCard({ insights }: InsightCardProps) {
  return (
    <AppCard tone="subtle" style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Insights</Text>
        <Text style={styles.subtitle}>Simple patterns from recent logs</Text>
      </View>

      <View style={styles.list}>
        {insights.map((insight, index) => (
          <View key={`${insight}-${index}`} style={styles.item}>
            <View style={styles.marker} />
            <Text style={styles.itemText}>{insight}</Text>
          </View>
        ))}
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  headerRow: {
    gap: spacing.xxs
  },
  item: {
    alignItems: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md
  },
  itemText: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1
  },
  list: {
    gap: spacing.sm
  },
  marker: {
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
    height: 8,
    marginTop: 6,
    width: 8
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
