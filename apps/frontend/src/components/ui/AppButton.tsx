import { Pressable, StyleSheet, Text } from "react-native";
import type { StyleProp, ViewStyle } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type AppButtonVariant = "primary" | "neutral" | "danger" | "outline";

type AppButtonProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  isLoading?: boolean;
  variant?: AppButtonVariant;
  style?: StyleProp<ViewStyle>;
  testID?: string;
};

function buttonVariantStyle(variant: AppButtonVariant): ViewStyle {
  if (variant === "outline") {
    return {
      backgroundColor: colors.surface,
      borderColor: colors.borderStrong,
      borderWidth: 1
    };
  }
  if (variant === "neutral") {
    return { backgroundColor: colors.textPrimary };
  }
  if (variant === "danger") {
    return { backgroundColor: colors.dangerText };
  }
  return { backgroundColor: colors.primary };
}

function textColor(variant: AppButtonVariant): string {
  if (variant === "outline") {
    return colors.textPrimary;
  }

  return colors.inverseText;
}

export default function AppButton({
  label,
  onPress,
  disabled = false,
  isLoading = false,
  variant = "primary",
  style,
  testID
}: AppButtonProps) {
  const isDisabled = disabled || isLoading;
  return (
    <Pressable
      accessibilityRole="button"
      disabled={isDisabled}
      onPress={onPress}
      style={[styles.button, buttonVariantStyle(variant), isDisabled ? styles.buttonDisabled : null, style]}
      testID={testID}
    >
      <Text style={[styles.buttonText, { color: textColor(variant) }]}>{isLoading ? `${label}...` : label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    borderRadius: radius.sm,
    borderWidth: 0,
    justifyContent: "center",
    minHeight: 42,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm
  },
  buttonDisabled: {
    opacity: 0.65
  },
  buttonText: {
    ...typography.button,
    textAlign: "center"
  }
});
