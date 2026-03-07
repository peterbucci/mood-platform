import { Pressable, StyleSheet, Text, View } from "react-native";

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
    gap: 8
  },
  label: {
    color: "#374151",
    fontSize: 14,
    fontWeight: "700"
  },
  helpText: {
    color: "#6b7280",
    fontSize: 13
  },
  options: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  option: {
    backgroundColor: "#f9fafb",
    borderColor: "#d1d5db",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  optionSelected: {
    backgroundColor: "#dcfce7",
    borderColor: "#16a34a"
  },
  optionDisabled: {
    opacity: 0.65
  },
  optionText: {
    color: "#374151",
    fontSize: 12,
    fontWeight: "700"
  },
  optionTextSelected: {
    color: "#166534"
  }
});
