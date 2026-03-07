import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
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
    gap: spacing.sm
  },
  label: {
    ...typography.bodyStrong,
    color: colors.textPrimary
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
    backgroundColor: colors.primary,
    borderColor: colors.primaryStrong
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
    color: colors.inverseText
  }
});
