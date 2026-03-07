import { StyleSheet, Text, View } from "react-native";

import { colors, typography } from "../../theme";
import AppCard from "../ui/AppCard";
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
    <AppCard>
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
    </AppCard>
  );
}

const styles = StyleSheet.create({
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  rows: {
    gap: 7
  },
  emptyText: {
    ...typography.helper,
    color: colors.textMuted,
    fontSize: 13,
    fontStyle: "italic"
  }
});
