import { StyleSheet, Text, View } from "react-native";

import type { MetricTone } from "../../utils/dashboardAnalytics";
import { colors, radius, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";
import { getDashboardCategoryTheme } from "./dashboardTheme";

type MetricCardProps = {
  detail: string;
  icon: string;
  label: string;
  tone: MetricTone;
  value: string;
};

function resolveTone(tone: MetricTone) {
  if (tone === "primary") {
    return {
      iconBackground: colors.infoSurface,
      iconBorder: colors.infoBorder,
      iconText: colors.primaryStrong
    };
  }

  if (tone === "neutral") {
    return {
      iconBackground: colors.surfaceMuted,
      iconBorder: colors.border,
      iconText: colors.textSecondary
    };
  }

  const theme = getDashboardCategoryTheme(tone);
  return {
    iconBackground: theme.softSurface,
    iconBorder: theme.border,
    iconText: theme.line
  };
}

export default function MetricCard({ detail, icon, label, tone, value }: MetricCardProps) {
  const toneStyle = resolveTone(tone);

  return (
    <AppCard style={styles.card}>
      <View style={styles.headerRow}>
        <View
          style={[
            styles.iconBadge,
            { backgroundColor: toneStyle.iconBackground, borderColor: toneStyle.iconBorder }
          ]}
        >
          <Text style={[styles.iconText, { color: toneStyle.iconText }]}>{icon}</Text>
        </View>
        <Text numberOfLines={1} style={styles.detail}>
          {detail}
        </Text>
      </View>
      <Text numberOfLines={1} style={styles.value}>
        {value}
      </Text>
      <Text style={styles.label}>{label}</Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.sm,
    minHeight: 132
  },
  detail: {
    ...typography.helper,
    color: colors.textMuted,
    flexShrink: 1,
    textAlign: "right"
  },
  headerRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  iconBadge: {
    alignItems: "center",
    borderRadius: radius.sm,
    borderWidth: 1,
    height: 34,
    justifyContent: "center",
    minWidth: 46,
    paddingHorizontal: spacing.xs
  },
  iconText: {
    ...typography.helper,
    fontWeight: "700"
  },
  label: {
    ...typography.body,
    color: colors.textSecondary
  },
  value: {
    ...typography.title,
    color: colors.textPrimary,
    fontSize: 22
  }
});
