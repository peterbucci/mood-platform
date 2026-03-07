import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type FitbitStatusIndicatorTone = "success" | "neutral" | "warning";

type FitbitStatusIndicatorProps = {
  label: string;
  tone: FitbitStatusIndicatorTone;
};

function resolveTone(tone: FitbitStatusIndicatorTone) {
  if (tone === "success") {
    return {
      backgroundColor: colors.successSurface,
      borderColor: colors.successBorder,
      dotColor: colors.successText,
      textColor: colors.successText
    };
  }

  if (tone === "warning") {
    return {
      backgroundColor: colors.warningSurface,
      borderColor: colors.warningBorder,
      dotColor: colors.warningText,
      textColor: colors.warningText
    };
  }

  return {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.borderStrong,
    dotColor: colors.textMuted,
    textColor: colors.textSecondary
  };
}

export default function FitbitStatusIndicator({ label, tone }: FitbitStatusIndicatorProps) {
  const toneStyle = resolveTone(tone);

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: toneStyle.backgroundColor,
          borderColor: toneStyle.borderColor
        }
      ]}
    >
      <View style={[styles.dot, { backgroundColor: toneStyle.dotColor }]} />
      <Text style={[styles.label, { color: toneStyle.textColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignItems: "center",
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs
  },
  dot: {
    borderRadius: radius.pill,
    height: 8,
    width: 8
  },
  label: {
    ...typography.helper,
    fontWeight: "700"
  }
});
