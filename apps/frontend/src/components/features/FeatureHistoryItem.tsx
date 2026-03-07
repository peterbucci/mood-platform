import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { FeatureRecord } from "../../types/features";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import {
  countFeatureDataGroups,
  formatFeatureCaptureTime,
  formatFeatureRelativeTime,
  formatFeatureSource,
  shortenFeatureId
} from "../../utils/featureHistoryFormatting";
import FeatureMoodBadge from "./FeatureMoodBadge";

type FeatureHistoryItemProps = {
  feature: FeatureRecord;
  nowMs?: number;
  onPress: (featureId: string) => void;
  showDivider?: boolean;
};

function pluralizeDataGroup(count: number): string {
  return `${count} data ${count === 1 ? "group" : "groups"}`;
}

export default function FeatureHistoryItem({
  feature,
  nowMs = Date.now(),
  onPress,
  showDivider = false
}: FeatureHistoryItemProps) {
  const mood = getMoodDisplayModel(feature.label);
  const title = mood.state === "labeled" && mood.emotion ? mood.emotion : mood.text;
  const captureText = formatFeatureCaptureTime(feature.createdAt, nowMs);
  const subtitle = mood.state === "labeled" ? `${mood.categoryLabel} • ${captureText}` : captureText;
  const metaItems = [formatFeatureSource(feature.source)];
  const dataGroupCount = countFeatureDataGroups(feature.data);

  if (dataGroupCount > 0) {
    metaItems.push(pluralizeDataGroup(dataGroupCount));
  }

  metaItems.push(`ID ${shortenFeatureId(feature.id)}`);

  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => onPress(feature.id)}
      style={({ pressed }) => [
        styles.item,
        showDivider ? styles.itemDivider : null,
        pressed ? styles.itemPressed : null
      ]}
      testID={`feature-history-item-${feature.id}`}
    >
      <View style={styles.topRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
        <Text style={styles.relativeTime}>{formatFeatureRelativeTime(feature.createdAt, nowMs)}</Text>
      </View>

      <View style={styles.badgeRow}>
        <FeatureMoodBadge
          category={mood.state === "labeled" ? feature.label?.category : null}
          fallbackLabel={mood.text}
        />
      </View>

      <View style={styles.bottomRow}>
        <Text numberOfLines={1} style={styles.meta}>
          {metaItems.join(" • ")}
        </Text>
        <Text style={styles.action}>View details</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  action: {
    ...typography.helper,
    color: colors.primaryStrong,
    fontWeight: "700"
  },
  badgeRow: {
    gap: spacing.xs
  },
  bottomRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  item: {
    backgroundColor: colors.surfaceMuted,
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md
  },
  itemDivider: {
    borderTopColor: colors.border,
    borderTopWidth: 1
  },
  itemPressed: {
    backgroundColor: colors.infoSurface
  },
  meta: {
    ...typography.helper,
    color: colors.textMuted,
    flex: 1
  },
  relativeTime: {
    ...typography.helper,
    color: colors.textMuted,
    textAlign: "right"
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  titleBlock: {
    flex: 1,
    gap: spacing.xxs
  },
  topRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  }
});
