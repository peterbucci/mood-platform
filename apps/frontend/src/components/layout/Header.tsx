import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

type HeaderProps = {
  appName?: string;
  currentRouteName?: string;
  children?: ReactNode;
};

export default function Header({
  appName = "Mood Platform",
  currentRouteName,
  children
}: HeaderProps) {
  return (
    <View style={styles.container}>
      <View style={styles.titleBlock}>
        <Text style={styles.title}>{appName}</Text>
        {currentRouteName ? <Text style={styles.subtitle}>{currentRouteName}</Text> : null}
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
  titleBlock: {
    gap: spacing.xxs
  },
  title: {
    ...typography.title,
    color: colors.textPrimary
  },
  subtitle: {
    ...typography.body,
    color: colors.textMuted
  }
});
