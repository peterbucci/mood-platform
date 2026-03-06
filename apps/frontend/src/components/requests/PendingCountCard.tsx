import { StyleSheet, Text, View } from "react-native";

type PendingCountCardProps = {
  pendingCount: number;
};

export default function PendingCountCard({ pendingCount }: PendingCountCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>Pending Requests</Text>
      <Text style={styles.value} testID="pending-count-value">
        {pendingCount}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#eff6ff",
    borderColor: "#bfdbfe",
    borderRadius: 12,
    borderWidth: 1,
    gap: 6,
    padding: 14
  },
  label: {
    color: "#1e3a8a",
    fontSize: 13,
    fontWeight: "600"
  },
  value: {
    color: "#1d4ed8",
    fontSize: 28,
    fontWeight: "800"
  }
});
