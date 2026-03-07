import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import StatusBadge from "./StatusBadge";

type RequestRowProps = {
  onPressFeature?: (featureId: string) => void;
  request: FeatureRequestRecord;
};

function formatTimestamp(createdAt: number): string {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return String(createdAt);
  }
  return parsed.toLocaleString();
}

export default function RequestRow({ onPressFeature, request }: RequestRowProps) {
  const featureId = request.featureId;

  return (
    <View style={styles.row}>
      <Text style={styles.requestId}>Request ID: {request.id}</Text>
      <StatusBadge status={request.status} />
      <Text style={styles.meta}>Created: {formatTimestamp(request.createdAt)}</Text>
      <Text style={styles.meta}>Source: {request.source}</Text>
      {featureId ? (
        <View style={styles.featureContainer}>
          <Text style={styles.meta}>Feature ID: {featureId}</Text>
          {onPressFeature ? (
            <Pressable
              accessibilityRole="button"
              onPress={() => onPressFeature(featureId)}
              style={styles.featureButton}
            >
              <Text style={styles.featureButtonText}>View Feature</Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}
    </View>
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
  requestId: {
    color: "#111827",
    fontSize: 14,
    fontWeight: "700"
  },
  meta: {
    color: "#4b5563",
    fontSize: 12
  },
  featureContainer: {
    gap: 6
  },
  featureButton: {
    alignSelf: "flex-start",
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  featureButtonText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700"
  }
});
