import { StyleSheet, Text, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import StatusBadge from "./StatusBadge";

type RequestRowProps = {
  request: FeatureRequestRecord;
};

function formatTimestamp(createdAt: number): string {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return String(createdAt);
  }
  return parsed.toLocaleString();
}

export default function RequestRow({ request }: RequestRowProps) {
  return (
    <View style={styles.row}>
      <Text style={styles.requestId}>Request ID: {request.id}</Text>
      <StatusBadge status={request.status} />
      <Text style={styles.meta}>Created: {formatTimestamp(request.createdAt)}</Text>
      <Text style={styles.meta}>Source: {request.source}</Text>
      {request.featureId ? <Text style={styles.meta}>Feature ID: {request.featureId}</Text> : null}
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
  }
});
