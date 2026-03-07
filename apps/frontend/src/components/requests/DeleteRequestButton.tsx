import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type DeleteRequestButtonProps = {
  disabled?: boolean;
  isLoading?: boolean;
  onPress: () => void;
};

export default function DeleteRequestButton({
  disabled = false,
  isLoading = false,
  onPress
}: DeleteRequestButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || isLoading}
      onPress={onPress}
      style={[styles.button, disabled || isLoading ? styles.buttonDisabled : null]}
      testID="request-delete-button"
    >
      <Text style={styles.buttonText}>{isLoading ? "Deleting..." : "Delete"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: "flex-start",
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
