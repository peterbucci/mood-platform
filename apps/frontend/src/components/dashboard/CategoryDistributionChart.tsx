import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { DashboardDistributionItem, DashboardTimeframe } from "../../utils/dashboardAnalytics";
import AppCard from "../ui/AppCard";
import { getDashboardCategoryTheme } from "./dashboardTheme";

type CategoryDistributionChartProps = {
  distribution: DashboardDistributionItem[];
  timeframe: DashboardTimeframe;
};

export default function CategoryDistributionChart({
  distribution,
  timeframe
}: CategoryDistributionChartProps) {
  return (
    <AppCard style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Category Distribution</Text>
        <Text style={styles.subtitle}>Last {timeframe} days</Text>
      </View>

      <View style={styles.rows}>
        {distribution.map((item) => {
          const theme = getDashboardCategoryTheme(item.category);
          const width = item.count > 0 ? Math.max(item.share * 100, 8) : 0;

          return (
            <View key={item.category} style={styles.row}>
              <Text style={styles.label}>{item.label}</Text>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      backgroundColor: theme.bar,
                      borderColor: theme.border,
                      width: `${width}%`
                    }
                  ]}
                />
              </View>
              <Text style={styles.value}>
                {Math.round(item.share * 100)}%
                {item.count > 0 ? ` | ${item.count}` : ""}
              </Text>
            </View>
          );
        })}
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  barFill: {
    borderRadius: radius.pill,
    borderWidth: 1,
    height: 10
  },
  barTrack: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    flex: 1,
    height: 10,
    overflow: "hidden"
  },
  card: {
    gap: spacing.md
  },
  headerRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  label: {
    ...typography.bodyStrong,
    color: colors.textPrimary,
    minWidth: 88
  },
  rows: {
    gap: spacing.md
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  subtitle: {
    ...typography.helper,
    color: colors.textMuted
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  value: {
    ...typography.helper,
    color: colors.textSecondary,
    minWidth: 54,
    textAlign: "right"
  }
});
