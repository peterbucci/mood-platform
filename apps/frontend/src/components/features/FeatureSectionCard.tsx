import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { FeatureSectionRow } from "../../utils/featureFormatting";
import AppCard from "../ui/AppCard";
import FeatureValueRow from "./FeatureValueRow";

type FeatureSectionCardProps = {
  rows: FeatureSectionRow[];
  subtitle?: string;
  title: string;
};

export default function FeatureSectionCard({ rows, subtitle, title }: FeatureSectionCardProps) {
  return (
    <AppCard>
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      <View style={styles.rows}>
        {rows.map((row, index) => (
          <FeatureValueRow
            key={`${title}-${row.id}`}
            label={row.label}
            showDivider={index > 0}
            value={row.value}
          />
        ))}
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: spacing.xxs
  },
  rows: {
    gap: 0
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
