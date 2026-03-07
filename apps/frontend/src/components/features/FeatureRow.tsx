import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { FeatureRecord } from "../../types/features";
import { getMoodDisplayModel } from "../../utils/moodFormatting";

type FeatureRowProps = {
  feature: FeatureRecord;
  onPress: (featureId: string) => void;
};

function formatTimestamp(createdAt: number): string {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return String(createdAt);
  }
  return parsed.toLocaleString();
}

export default function FeatureRow({ feature, onPress }: FeatureRowProps) {
  const mood = getMoodDisplayModel(feature.label);

  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => onPress(feature.id)}
      style={styles.row}
      testID={`feature-row-${feature.id}`}
    >
      <Text style={styles.captureTime}>Feature ID: {feature.id}</Text>
      <Text style={styles.meta}>Captured: {formatTimestamp(feature.createdAt)}</Text>
      <Text style={styles.meta}>Mood: {mood.text}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.xxs,
    minHeight: 84,
    padding: spacing.md
  },
  captureTime: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  meta: {
    ...typography.helper,
    color: colors.textSecondary
  }
});
