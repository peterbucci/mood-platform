import { StyleSheet, Text } from "react-native";
import type { StyleProp, ViewStyle } from "react-native";

import { colors, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";

type RequestSummaryTone = "neutral" | "info" | "success" | "warning";

type RequestSummaryCardProps = {
  detail: string;
  label: string;
  style?: StyleProp<ViewStyle>;
  testID?: string;
  tone?: RequestSummaryTone;
  value: string;
};

function resolveTone(tone: RequestSummaryTone): "default" | "info" | "success" | "warning" {
  if (tone === "info") {
    return "info";
  }
  if (tone === "success") {
    return "success";
  }
  if (tone === "warning") {
    return "warning";
  }

  return "default";
}

function resolveValueColor(tone: RequestSummaryTone): string {
  if (tone === "info") {
    return colors.primaryStrong;
  }
  if (tone === "success") {
    return colors.successText;
  }
  if (tone === "warning") {
    return colors.warningText;
  }

  return colors.textPrimary;
}

export default function RequestSummaryCard({
  detail,
  label,
  style,
  testID,
  tone = "neutral",
  value
}: RequestSummaryCardProps) {
  return (
    <AppCard style={[styles.card, style]} testID={testID} tone={resolveTone(tone)}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, { color: resolveValueColor(tone) }]}>{value}</Text>
      <Text style={styles.detail}>{detail}</Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.xxs,
    minHeight: 104,
    padding: spacing.md
  },
  detail: {
    ...typography.helper,
    color: colors.textMuted
  },
  label: {
    ...typography.helper,
    color: colors.textSecondary,
    textTransform: "uppercase"
  },
  value: {
    ...typography.title,
    fontSize: 22
  }
});
