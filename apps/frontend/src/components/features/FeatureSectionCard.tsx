import { StyleSheet, Text, View } from "react-native";

import type { FeatureSectionRow } from "../../utils/featureFormatting";
import FeatureValueRow from "./FeatureValueRow";

type FeatureSectionCardProps = {
  title: string;
  rows: FeatureSectionRow[];
};

export default function FeatureSectionCard({ title, rows }: FeatureSectionCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.rows}>
        {rows.map((row) => (
          <FeatureValueRow key={`${title}-${row.label}`} label={row.label} value={row.value} />
        ))}
      </View>
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
  }
});
