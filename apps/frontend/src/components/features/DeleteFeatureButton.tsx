import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type DeleteFeatureButtonProps = {
  disabled?: boolean;
  isLoading?: boolean;
  onPress: () => void;
};

export default function DeleteFeatureButton({
  disabled = false,
  isLoading = false,
  onPress
}: DeleteFeatureButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || isLoading}
      onPress={onPress}
      style={[styles.button, disabled || isLoading ? styles.buttonDisabled : null]}
      testID="feature-delete-button"
    >
      <Text style={styles.buttonText}>{isLoading ? "Deleting..." : "Delete Snapshot"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.surface,
    borderColor: colors.dangerBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  buttonDisabled: {
    opacity: 0.65
  },
  buttonText: {
    ...typography.helper,
    color: colors.dangerText,
    fontWeight: "700"
  }
});
