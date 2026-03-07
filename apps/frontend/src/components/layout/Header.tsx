import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

type HeaderProps = {
  appName?: string;
  children?: ReactNode;
};

export default function Header({
  appName = "Mood Platform",
  children
}: HeaderProps) {
  return (
    <View style={styles.container}>
      <View style={styles.titleBlock}>
        <Text style={styles.title}>{appName}</Text>
        <Text style={styles.subtitle}>Track mood and understand your daily signals.</Text>
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderBottomColor: colors.borderStrong,
    borderBottomWidth: 1,
    gap: spacing.sm,
    paddingBottom: spacing.md
  },
  subtitle: {
    ...typography.body,
    color: colors.textMuted
  },
  title: {
    ...typography.title,
    color: colors.textPrimary
  },
  titleBlock: {
    gap: spacing.xxs
  }
});
