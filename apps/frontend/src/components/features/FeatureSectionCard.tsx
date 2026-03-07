import { StyleSheet, Text, View } from "react-native";

import { colors, typography } from "../../theme";
import type { FeatureSectionRow } from "../../utils/featureFormatting";
import AppCard from "../ui/AppCard";
import FeatureValueRow from "./FeatureValueRow";

type FeatureSectionCardProps = {
  title: string;
  rows: FeatureSectionRow[];
};

export default function FeatureSectionCard({ title, rows }: FeatureSectionCardProps) {
  return (
    <AppCard>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.rows}>
        {rows.map((row) => (
          <FeatureValueRow key={`${title}-${row.label}`} label={row.label} value={row.value} />
        ))}
      </View>
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
  }
});
