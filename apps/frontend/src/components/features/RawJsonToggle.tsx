import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { colors, radius, spacing, typography } from "../../theme";

type RawJsonToggleProps = {
  payload: unknown;
  showToggle?: boolean;
};

export default function RawJsonToggle({ payload, showToggle = true }: RawJsonToggleProps) {
  const [expanded, setExpanded] = useState(!showToggle);

  const rawJson = useMemo(() => {
    try {
      return JSON.stringify(payload, null, 2);
    } catch {
      return String(payload);
    }
  }, [payload]);

  return (
    <View style={styles.container}>
      {showToggle ? (
        <Pressable
          accessibilityRole="button"
          onPress={() => setExpanded((current) => !current)}
          style={styles.button}
        >
          <Text style={styles.buttonText}>{expanded ? "Hide Raw JSON" : "Show Raw JSON"}</Text>
        </Pressable>
      ) : null}
      {expanded ? (
        <View style={styles.rawContainer}>
          <Text selectable style={styles.rawText}>
            {rawJson}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm
  },
  button: {
    alignSelf: "flex-start",
    backgroundColor: colors.textPrimary,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  buttonText: {
    ...typography.helper,
    color: colors.inverseText,
    fontWeight: "700"
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
  }
});
