import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import type { MoodCategory } from "../../types/mood";
import { getEmotionOptionsForCategory } from "../../utils/moodTaxonomy";

type EmotionSelectorProps = {
  category: MoodCategory | null;
  disabled?: boolean;
  onSelectEmotion: (emotion: string) => void;
  selectedEmotion: string | null;
};

function toEmotionTestId(emotion: string): string {
  return emotion.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

export default function EmotionSelector({
  category,
  disabled = false,
  onSelectEmotion,
  selectedEmotion
}: EmotionSelectorProps) {
  const options = getEmotionOptionsForCategory(category);

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Emotion</Text>
      {!category ? (
        <Text style={styles.helpText}>Select a category first.</Text>
      ) : (
        <View style={styles.options}>
          {options.map((emotion) => {
            const selected = selectedEmotion === emotion;
            return (
              <Pressable
                accessibilityRole="button"
                disabled={disabled}
                key={emotion}
                onPress={() => onSelectEmotion(emotion)}
                style={[styles.option, selected ? styles.optionSelected : null, disabled ? styles.optionDisabled : null]}
                testID={`mood-emotion-option-${toEmotionTestId(emotion)}`}
              >
                <Text style={[styles.optionText, selected ? styles.optionTextSelected : null]}>
                  {emotion}
                </Text>
              </Pressable>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm
  },
  label: {
    ...typography.bodyStrong,
    color: colors.textSecondary
  },
  helpText: {
    ...typography.helper,
    color: colors.textMuted
  },
  options: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  option: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.neutralBorder,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  optionSelected: {
    backgroundColor: colors.calmSurface,
    borderColor: colors.calmBorder
  },
  optionDisabled: {
    opacity: 0.65
  },
  optionText: {
    ...typography.helper,
    color: colors.textSecondary,
    fontWeight: "700"
  },
  optionTextSelected: {
    color: colors.calmText
  }
});
