import type { ReactNode } from "react";
import { StyleSheet, View } from "react-native";
import type { StyleProp, ViewStyle } from "react-native";

import { colors, radius, spacing } from "../../theme";

type AppCardTone = "default" | "subtle" | "info" | "success" | "warning" | "danger";

type AppCardProps = {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  testID?: string;
  tone?: AppCardTone;
};

function toneStyle(tone: AppCardTone): ViewStyle {
  if (tone === "subtle") {
    return { backgroundColor: colors.surfaceMuted, borderColor: colors.borderStrong };
  }
  if (tone === "info") {
    return { backgroundColor: colors.infoSurface, borderColor: colors.infoBorder };
  }
  if (tone === "success") {
    return { backgroundColor: colors.successSurface, borderColor: colors.successBorder };
  }
  if (tone === "warning") {
    return { backgroundColor: colors.warningSurface, borderColor: colors.warningBorder };
  }
  if (tone === "danger") {
    return { backgroundColor: colors.dangerSurface, borderColor: colors.dangerBorder };
  }
  return { backgroundColor: colors.surface, borderColor: colors.border };
}

export default function AppCard({ children, style, testID, tone = "default" }: AppCardProps) {
  return (
    <View style={[styles.card, toneStyle(tone), style]} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.lg
  }
});
