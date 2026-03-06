import { StyleSheet, Text, View } from "react-native";

import FeatureValueRow from "./FeatureValueRow";

type FeatureRow = {
  label: string;
  value: string;
};

type FeatureSectionCardProps = {
  title: string;
  rows: FeatureRow[];
};

export default function FeatureSectionCard({ title, rows }: FeatureSectionCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {rows.length > 0 ? (
        <View style={styles.rows}>
          {rows.map((row) => (
            <FeatureValueRow key={`${title}-${row.label}`} label={row.label} value={row.value} />
          ))}
        </View>
      ) : (
        <Text style={styles.emptyText}>No values in this section for the latest snapshot.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
    padding: 14
  },
  title: {
    color: "#111827",
    fontSize: 16,
    fontWeight: "700"
  },
  rows: {
    gap: 7
  },
  emptyText: {
    color: "#6b7280",
    fontSize: 13,
    fontStyle: "italic"
  }
});
