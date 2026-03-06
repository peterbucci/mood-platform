import { StyleSheet, Text, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";

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

function statusColor(status: FeatureRequestRecord["status"]): string {
  if (status === "fulfilled") {
    return "#065f46";
  }
  if (status === "canceled") {
    return "#991b1b";
  }
  return "#9a3412";
}

export default function RequestRow({ request }: RequestRowProps) {
  return (
    <View style={styles.row}>
      <Text style={styles.requestId}>Request ID: {request.id}</Text>
      <Text style={[styles.status, { color: statusColor(request.status) }]}>
        Status: {request.status}
      </Text>
      <Text style={styles.meta}>Created: {formatTimestamp(request.createdAt)}</Text>
      <Text style={styles.meta}>Source: {request.source}</Text>
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
  status: {
    fontSize: 13,
    fontWeight: "700"
  },
  meta: {
    color: "#4b5563",
    fontSize: 12
  }
});
