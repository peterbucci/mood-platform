import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { FeatureRequestRecord } from "../../types/requests";
import {
  formatRequestRelativeTime,
  formatRequestSource,
  formatRequestTimestamp,
  shortenRequestId
} from "../../utils/requestFormatting";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import MoodBadge from "../mood/MoodBadge";
import DeleteRequestButton from "./DeleteRequestButton";
import RequestMetaRow from "./RequestMetaRow";
import StatusBadge from "./StatusBadge";

type RequestListItemProps = {
  deleteError?: string;
  isDeleting?: boolean;
  onPressDelete?: (requestId: string) => void;
  onPressFeature?: (featureId: string) => void;
  request: FeatureRequestRecord;
  showDivider?: boolean;
};

export default function RequestListItem({
  deleteError,
  isDeleting = false,
  onPressDelete,
  onPressFeature,
  request,
  showDivider = false
}: RequestListItemProps) {
  const featureId = request.featureId;
  const mood = getMoodDisplayModel(request.label);

  return (
    <View style={[styles.item, showDivider ? styles.itemDivider : null]} testID={`request-item-${request.id}`}>
      <View style={styles.topRow}>
        <View style={styles.topRowLeft}>
          <StatusBadge status={request.status} />
          <View style={styles.sourcePill}>
            <Text style={styles.sourceText}>{formatRequestSource(request.source)}</Text>
          </View>
        </View>
        <Text style={styles.relativeTime}>{formatRequestRelativeTime(request.createdAt)}</Text>
      </View>

      <View style={styles.content}>
        {mood.state === "labeled" && mood.emotion ? (
          <View style={styles.moodRow}>
            <MoodBadge category={request.label?.category} />
            <Text style={styles.moodEmotion}>{mood.emotion}</Text>
          </View>
        ) : (
          <Text style={styles.unlabeledMood}>Mood not labeled</Text>
        )}

        <RequestMetaRow
          items={[formatRequestTimestamp(request.createdAt), `ID ${shortenRequestId(request.id)}`]}
        />

        {featureId ? <Text style={styles.featureReadyText}>Feature snapshot ready to review.</Text> : null}

        {featureId || onPressDelete ? (
          <View style={styles.actionsRow}>
            {featureId && onPressFeature ? (
              <Pressable
                accessibilityRole="button"
                onPress={() => onPressFeature(featureId)}
                style={styles.featureButton}
              >
                <Text style={styles.featureButtonText}>View feature details</Text>
              </Pressable>
            ) : null}
            {onPressDelete ? (
              <DeleteRequestButton
                disabled={isDeleting}
                isLoading={isDeleting}
                onPress={() => onPressDelete(request.id)}
              />
            ) : null}
          </View>
        ) : null}

        {deleteError ? <Text style={styles.deleteError}>{deleteError}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  actionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  deleteError: {
    ...typography.helper,
    color: colors.dangerText,
    fontWeight: "600"
  },
  content: {
    gap: spacing.xs
  },
  featureButton: {
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: colors.infoSurface,
    borderColor: colors.infoBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    minHeight: 34,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  featureButtonText: {
    ...typography.helper,
    color: colors.primaryStrong,
    fontWeight: "700"
  },
  featureReadyText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  item: {
    gap: spacing.sm,
    paddingVertical: spacing.md
  },
  itemDivider: {
    borderTopColor: colors.border,
    borderTopWidth: 1
  },
  moodEmotion: {
    ...typography.bodyStrong,
    color: colors.textPrimary,
    flexShrink: 1
  },
  moodRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  relativeTime: {
    ...typography.helper,
    color: colors.textMuted
  },
  sourcePill: {
    backgroundColor: colors.neutralSurface,
    borderColor: colors.neutralBorder,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs
  },
  sourceText: {
    ...typography.helper,
    color: colors.neutralText,
    fontWeight: "700"
  },
  topRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between"
  },
  topRowLeft: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    flexShrink: 1
  },
  unlabeledMood: {
    ...typography.body,
    color: colors.textSecondary
  }
});
