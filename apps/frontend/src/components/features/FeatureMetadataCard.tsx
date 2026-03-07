import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { FeatureMetadataViewModel } from "../../utils/featureFormatting";
import AppCard from "../ui/AppCard";
import FeatureValueRow from "./FeatureValueRow";

type FeatureMetadataCardProps = {
  metadata: FeatureMetadataViewModel;
};

export default function FeatureMetadataCard({ metadata }: FeatureMetadataCardProps) {
  return (
    <AppCard tone="subtle">
      <View style={styles.header}>
        <Text style={styles.title}>Metadata</Text>
        <Text style={styles.subtitle}>Technical context for this snapshot.</Text>
      </View>
      <View style={styles.rows}>
        <FeatureValueRow label="Source" value={metadata.source} />
        <FeatureValueRow label="Created At" showDivider value={metadata.createdAt} />
        <FeatureValueRow label="Extractor Version" showDivider value={metadata.extractorVersion} />
        <FeatureValueRow label="Window Start" showDivider value={metadata.windowStart} />
        <FeatureValueRow label="Window End" showDivider value={metadata.windowEnd} />
        <FeatureValueRow label="Source Timezone" showDivider value={metadata.sourceTimezone} />
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
