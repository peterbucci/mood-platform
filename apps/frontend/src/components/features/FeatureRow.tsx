import { Pressable, StyleSheet, Text } from "react-native";

import type { FeatureRecord } from "../../types/features";

type FeatureRowProps = {
  feature: FeatureRecord;
  onPress: (featureId: string) => void;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function formatTimestamp(createdAt: number): string {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return String(createdAt);
  }
  return parsed.toLocaleString();
}

function getSummaryIndicator(feature: FeatureRecord): string {
  const summaryMetadata = isRecord(feature.summaryMetadata) ? feature.summaryMetadata : null;
  if (summaryMetadata) {
    const summaryFields = Object.keys(summaryMetadata).length;
    return `${summaryFields} summary field${summaryFields === 1 ? "" : "s"}`;
  }

  const sectionCount = Object.keys(feature.data).length;
  return `${sectionCount} section${sectionCount === 1 ? "" : "s"}`;
}

export default function FeatureRow({ feature, onPress }: FeatureRowProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => onPress(feature.id)}
      style={styles.row}
      testID={`feature-row-${feature.id}`}
    >
      <Text style={styles.captureTime}>Capture: {formatTimestamp(feature.createdAt)}</Text>
      <Text style={styles.meta}>Source: {feature.source}</Text>
      <Text style={styles.meta}>Summary: {getSummaryIndicator(feature)}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 10,
    borderWidth: 1,
    gap: 4,
    padding: 12
  },
  captureTime: {
    color: "#111827",
    fontSize: 14,
    fontWeight: "700"
  },
  meta: {
    color: "#4b5563",
    fontSize: 12
  }
});
