import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { MoodLabelValue } from "../../types/mood";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import AppCard from "../ui/AppCard";
import MoodBadge from "./MoodBadge";

type MoodLabelCardProps = {
  label: MoodLabelValue;
};

export default function MoodLabelCard({ label }: MoodLabelCardProps) {
  const mood = getMoodDisplayModel(label);

  return (
    <AppCard>
      <Text style={styles.title}>Mood</Text>
      {mood.state === "labeled" && mood.emotion ? (
        <View style={styles.labeledRow}>
          <MoodBadge category={label?.category} />
          <Text style={styles.labeledText}>- {mood.emotion}</Text>
        </View>
      ) : (
        <Text style={styles.fallbackText}>{mood.text}</Text>
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  labeledRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  labeledText: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  fallbackText: {
    ...typography.bodyStrong,
    color: colors.textSecondary
  }
});
