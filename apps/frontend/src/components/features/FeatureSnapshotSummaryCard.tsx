import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { MoodLabelValue } from "../../types/mood";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import AppCard from "../ui/AppCard";
import MoodBadge from "../mood/MoodBadge";

type FeatureSnapshotSummaryCardProps = {
  capturedAt: string;
  capturedRelative: string;
  contextLine: string;
  label: MoodLabelValue;
  moodActionLabel: string;
  onPressMoodAction: () => void;
  sourceLabel: string;
};

export default function FeatureSnapshotSummaryCard({
  capturedAt,
  capturedRelative,
  contextLine,
  label,
  moodActionLabel,
  onPressMoodAction,
  sourceLabel
}: FeatureSnapshotSummaryCardProps) {
  const mood = getMoodDisplayModel(label);

  return (
    <AppCard tone="info" style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>Snapshot Summary</Text>
        <Text style={styles.relativeTime}>{capturedRelative}</Text>
      </View>

      <View style={styles.moodBlock}>
        <Text style={styles.moodLabel}>Mood Label</Text>
        {mood.state === "labeled" && mood.emotion ? (
          <View style={styles.labeledRow}>
            <MoodBadge category={label?.category} />
            <Text style={styles.moodValue}>{mood.emotion}</Text>
          </View>
        ) : (
          <Text style={styles.moodValue}>{mood.text}</Text>
        )}
        <Text style={styles.contextText}>{contextLine}</Text>
      </View>

      <View style={styles.metaGrid}>
        <View style={styles.metaItem}>
          <Text style={styles.metaLabel}>Captured</Text>
          <Text style={styles.metaValue}>{capturedAt}</Text>
        </View>
        <View style={styles.metaItem}>
          <Text style={styles.metaLabel}>Source</Text>
          <Text style={styles.metaValue}>{sourceLabel}</Text>
        </View>
      </View>

      <Pressable
        accessibilityRole="button"
        onPress={onPressMoodAction}
        style={({ pressed }) => [styles.actionButton, pressed ? styles.actionButtonPressed : null]}
        testID="feature-detail-mood-action"
      >
        <Text style={styles.actionText}>{moodActionLabel}</Text>
      </Pressable>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.infoBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    minHeight: 38,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  actionButtonPressed: {
    opacity: 0.75
  },
  actionText: {
    ...typography.helper,
    color: colors.primaryStrong,
    fontWeight: "700"
  },
  card: {
    gap: spacing.md
  },
  contextText: {
    ...typography.body,
    color: colors.textSecondary
  },
  eyebrow: {
    ...typography.helper,
    color: colors.infoText,
    fontWeight: "700"
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md
  },
  labeledRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  metaGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md
  },
  metaItem: {
    flex: 1,
    gap: spacing.xxs,
    minWidth: 140
  },
  metaLabel: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  metaValue: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  moodBlock: {
    gap: spacing.xs
  },
  moodLabel: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  moodValue: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  },
  relativeTime: {
    ...typography.helper,
    color: colors.textMuted
  }
});
