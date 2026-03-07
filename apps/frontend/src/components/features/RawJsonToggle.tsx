import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

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
    <View style={styles.container}>
      <Pressable accessibilityRole="button" onPress={() => setExpanded((current) => !current)} style={styles.button}>
        <Text style={styles.buttonText}>{expanded ? "Hide Raw JSON" : "Show Raw JSON"}</Text>
      </Pressable>
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
    gap: 8
  },
  button: {
    alignSelf: "flex-start",
    backgroundColor: "#1f2937",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700"
  },
  rawContainer: {
    backgroundColor: "#0f172a",
    borderRadius: 12,
    padding: 12
  },
  rawText: {
    color: "#e2e8f0",
    fontFamily: "monospace",
    fontSize: 11
  }
});
