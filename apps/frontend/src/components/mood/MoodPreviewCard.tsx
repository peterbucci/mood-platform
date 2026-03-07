import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { MoodLabelValue } from "../../types/mood";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import AppCard from "../ui/AppCard";
import MoodBadge from "./MoodBadge";

type MoodPreviewCardProps = {
  label: MoodLabelValue;
};

export default function MoodPreviewCard({ label }: MoodPreviewCardProps) {
  const mood = getMoodDisplayModel(label);
  const hasSelection = mood.state === "labeled" && mood.emotion;

  return (
    <AppCard style={styles.card}>
      <Text style={styles.title}>Mood Preview</Text>
      {hasSelection ? (
        <View style={styles.previewRow}>
          <MoodBadge category={label?.category} />
          <Text style={styles.previewText}>{mood.emotion}</Text>
        </View>
      ) : (
        <Text style={styles.previewText}>{mood.text}</Text>
      )}
      <Text style={styles.helperText}>
        {hasSelection
          ? "This is the label that will be saved to the snapshot."
          : "Choose a category and emotion to preview the label before saving."}
      </Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.xs
  },
  helperText: {
    ...typography.body,
    color: colors.textSecondary
  },
  previewRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  previewText: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
