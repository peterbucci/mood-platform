import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type CancelRequestButtonProps = {
  disabled?: boolean;
  isLoading?: boolean;
  onPress: () => void;
};

export default function CancelRequestButton({
  disabled = false,
  isLoading = false,
  onPress
}: CancelRequestButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || isLoading}
      onPress={onPress}
      style={[
        styles.button,
        disabled || isLoading ? styles.buttonDisabled : null
      ]}
    >
      <Text style={styles.buttonText}>{isLoading ? "Canceling..." : "Cancel"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.dangerBorder,
    borderWidth: 1,
    borderRadius: radius.sm,
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
