import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type StatusBadgeTone =
  | "pending"
  | "fulfilled"
  | "canceled"
  | "energized"
  | "calm"
  | "stressed"
  | "tired"
  | "neutral";

type StatusBadgeProps = {
  label: string;
  tone: StatusBadgeTone;
};

function toneStyles(tone: StatusBadgeTone) {
  if (tone === "fulfilled") {
    return {
      badge: { backgroundColor: colors.successSurface, borderColor: colors.successBorder },
      text: { color: colors.successText }
    };
  }
  if (tone === "canceled") {
    return {
      badge: { backgroundColor: colors.neutralSurface, borderColor: colors.neutralBorder },
      text: { color: colors.neutralText }
    };
  }
  if (tone === "pending") {
    return {
      badge: { backgroundColor: colors.warningSurface, borderColor: colors.warningBorder },
      text: { color: colors.warningText }
    };
  }
  if (tone === "energized") {
    return {
      badge: { backgroundColor: colors.energizedSurface, borderColor: colors.energizedBorder },
      text: { color: colors.energizedText }
    };
  }
  if (tone === "calm") {
    return {
      badge: { backgroundColor: colors.calmSurface, borderColor: colors.calmBorder },
      text: { color: colors.calmText }
    };
  }
  if (tone === "stressed") {
    return {
      badge: { backgroundColor: colors.stressedSurface, borderColor: colors.stressedBorder },
      text: { color: colors.stressedText }
    };
  }
  if (tone === "tired") {
    return {
      badge: { backgroundColor: colors.tiredSurface, borderColor: colors.tiredBorder },
      text: { color: colors.tiredText }
    };
  }
  return {
    badge: { backgroundColor: colors.neutralSurface, borderColor: colors.neutralBorder },
    text: { color: colors.neutralText }
  };
}

export default function StatusBadge({ label, tone }: StatusBadgeProps) {
  const toneStyle = toneStyles(tone);
  return (
    <View style={[styles.badge, toneStyle.badge]}>
      <Text style={[styles.text, toneStyle.text]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xxs
  },
  text: {
    ...typography.badge
  }
});
