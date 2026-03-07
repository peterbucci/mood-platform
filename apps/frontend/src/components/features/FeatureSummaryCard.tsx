import { StyleSheet, Text } from "react-native";

import { colors, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";

type FeatureSummaryTone = "neutral" | "info" | "energized" | "calm" | "stressed" | "tired";

type FeatureSummaryCardProps = {
  detail: string;
  label: string;
  testID?: string;
  tone?: FeatureSummaryTone;
  value: string;
};

function toneStyles(tone: FeatureSummaryTone) {
  if (tone === "info") {
    return {
      card: { backgroundColor: colors.infoSurface, borderColor: colors.infoBorder },
      value: { color: colors.infoText }
    };
  }
  if (tone === "energized") {
    return {
      card: { backgroundColor: colors.energizedSurface, borderColor: colors.energizedBorder },
      value: { color: colors.energizedText }
    };
  }
  if (tone === "calm") {
    return {
      card: { backgroundColor: colors.calmSurface, borderColor: colors.calmBorder },
      value: { color: colors.calmText }
    };
  }
  if (tone === "stressed") {
    return {
      card: { backgroundColor: colors.stressedSurface, borderColor: colors.stressedBorder },
      value: { color: colors.stressedText }
    };
  }
  if (tone === "tired") {
    return {
      card: { backgroundColor: colors.tiredSurface, borderColor: colors.tiredBorder },
      value: { color: colors.tiredText }
    };
  }

  return {
    card: { backgroundColor: colors.surface, borderColor: colors.border },
    value: { color: colors.textPrimary }
  };
}

export default function FeatureSummaryCard({
  detail,
  label,
  testID,
  tone = "neutral",
  value
}: FeatureSummaryCardProps) {
  const toneStyle = toneStyles(tone);

  return (
    <AppCard style={[styles.card, toneStyle.card]} testID={testID}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, toneStyle.value]}>{value}</Text>
      <Text style={styles.detail}>{detail}</Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.xs,
    minHeight: 112
  },
  detail: {
    ...typography.helper,
    color: colors.textSecondary
  },
  label: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  value: {
    fontSize: 20,
    fontWeight: "700"
  }
});
