import { Pressable, StyleSheet, Text, View } from "react-native";

import type { MoodCategory } from "../../types/mood";
import { formatMoodCategory } from "../../utils/moodFormatting";
import { MOOD_CATEGORIES } from "../../utils/moodTaxonomy";

type CategorySelectorProps = {
  disabled?: boolean;
  onSelectCategory: (category: MoodCategory) => void;
  selectedCategory: MoodCategory | null;
};

export default function CategorySelector({
  disabled = false,
  onSelectCategory,
  selectedCategory
}: CategorySelectorProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Category</Text>
      <View style={styles.options}>
        {MOOD_CATEGORIES.map((category) => {
          const selected = selectedCategory === category;
          return (
            <Pressable
              accessibilityRole="button"
              disabled={disabled}
              key={category}
              onPress={() => onSelectCategory(category)}
              style={[styles.option, selected ? styles.optionSelected : null, disabled ? styles.optionDisabled : null]}
              testID={`mood-category-option-${category}`}
            >
              <Text style={[styles.optionText, selected ? styles.optionTextSelected : null]}>
                {formatMoodCategory(category)}
              </Text>
            </Pressable>
          );
        })}
      </View>
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
    backgroundColor: "#dbeafe",
    borderColor: "#2563eb"
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
    color: "#1d4ed8"
  }
});
