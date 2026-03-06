import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

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
    borderBottomColor: "#d1d5db",
    borderBottomWidth: 1,
    gap: 10,
    paddingBottom: 12
  },
  titleBlock: {
    gap: 2
  },
  title: {
    color: "#111827",
    fontSize: 24,
    fontWeight: "700"
  },
  subtitle: {
    color: "#6b7280",
    fontSize: 14
  }
});
