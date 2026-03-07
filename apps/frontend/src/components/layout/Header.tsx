import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { useAppRefresh } from "../../hooks/useAppRefresh";
import { colors, spacing, typography } from "../../theme";
import AppButton from "../ui/AppButton";

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
  const { triggerRefresh } = useAppRefresh();

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.title}>{appName}</Text>
          {currentRouteName ? <Text style={styles.subtitle}>{currentRouteName}</Text> : null}
        </View>
        <AppButton label="Refresh" onPress={triggerRefresh} style={styles.refreshButton} variant="neutral" />
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
  topRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  titleBlock: {
    flex: 1,
    gap: spacing.xxs,
    paddingRight: spacing.md
  },
  refreshButton: {
    minHeight: 36,
    minWidth: 98,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
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
