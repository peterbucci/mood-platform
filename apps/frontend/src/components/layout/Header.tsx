import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { Animated, Easing, Pressable, StyleSheet, Text, View } from "react-native";

import { useAppRefresh } from "../../hooks/useAppRefresh";
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
  const { isRefreshing, triggerRefresh } = useAppRefresh();
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!isRefreshing) {
      spin.stopAnimation();
      spin.setValue(0);
      return;
    }

    const animation = Animated.loop(
      Animated.timing(spin, {
        toValue: 1,
        duration: 700,
        easing: Easing.linear,
        useNativeDriver: true
      })
    );

    animation.start();

    return () => {
      animation.stop();
      spin.stopAnimation();
      spin.setValue(0);
    };
  }, [isRefreshing, spin]);

  const spinStyle = {
    transform: [
      {
        rotate: spin.interpolate({
          inputRange: [0, 1],
          outputRange: ["0deg", "360deg"]
        })
      }
    ]
  };

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.title}>{appName}</Text>
          {currentRouteName ? <Text style={styles.subtitle}>{currentRouteName}</Text> : null}
        </View>
        <Pressable
          accessibilityLabel="Refresh data"
          accessibilityRole="button"
          disabled={isRefreshing}
          onPress={triggerRefresh}
          style={({ pressed }) => [
            styles.refreshButton,
            isRefreshing ? styles.refreshButtonActive : null,
            pressed ? styles.refreshButtonPressed : null
          ]}
          testID="header-refresh-button"
        >
          <Animated.View style={spinStyle}>
            <Text style={[styles.refreshIcon, isRefreshing ? styles.refreshIconActive : null]}>↻</Text>
          </Animated.View>
        </Pressable>
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
    alignItems: "center",
    backgroundColor: colors.infoSurface,
    borderColor: colors.infoBorder,
    borderWidth: 1,
    borderRadius: 999,
    height: 42,
    justifyContent: "center",
    width: 42
  },
  refreshButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryStrong
  },
  refreshButtonPressed: {
    opacity: 0.9,
    transform: [{ scale: 0.96 }]
  },
  refreshIcon: {
    ...typography.bodyStrong,
    color: colors.textPrimary,
    fontSize: 20,
    lineHeight: 22
  },
  refreshIconActive: {
    color: colors.inverseText
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
