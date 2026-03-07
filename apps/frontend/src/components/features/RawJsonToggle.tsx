import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";

type RawJsonToggleProps = {
  payload: unknown;
};

export default function RawJsonToggle({ payload }: RawJsonToggleProps) {
  const [expanded, setExpanded] = useState(false);

  const rawJson = useMemo(() => {
    try {
      return JSON.stringify(payload, null, 2);
    } catch {
      return String(payload);
    }
  }, [payload]);

  return (
    <AppCard style={styles.container} tone="subtle">
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>Debug Data</Text>
          <Text style={styles.subtitle}>Advanced raw payload for troubleshooting.</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          onPress={() => setExpanded((current) => !current)}
          style={({ pressed }) => [styles.button, pressed ? styles.buttonPressed : null]}
          testID="feature-detail-raw-json-toggle"
        >
          <Text style={styles.buttonText}>{expanded ? "Hide Raw JSON" : "Show Raw JSON"}</Text>
        </Pressable>
      </View>
      {expanded ? (
        <View style={styles.rawContainer}>
          <Text selectable style={styles.rawText}>
            {rawJson}
          </Text>
        </View>
      ) : null}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: "flex-start",
    backgroundColor: colors.surface,
    borderColor: colors.borderStrong,
    borderRadius: radius.sm,
    borderWidth: 1,
    minHeight: 36,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  buttonPressed: {
    opacity: 0.75
  },
  buttonText: {
    ...typography.helper,
    color: colors.primaryStrong,
    fontWeight: "700"
  },
  container: {
    gap: spacing.md
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  headerCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  rawContainer: {
    backgroundColor: "#0f172a",
    borderRadius: radius.md,
    padding: spacing.md
  },
  rawText: {
    ...typography.helper,
    color: "#e2e8f0",
    fontFamily: "monospace",
    fontSize: 11
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
