import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type FeatureDateGroupProps = {
  children: ReactNode;
  title: string;
};

export default function FeatureDateGroup({ children, title }: FeatureDateGroupProps) {
  return (
    <View style={styles.group}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.items}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  group: {
    gap: spacing.sm
  },
  items: {
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    overflow: "hidden"
  },
  title: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  }
});
