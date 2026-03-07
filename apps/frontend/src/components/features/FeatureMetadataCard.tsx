import { StyleSheet, Text, View } from "react-native";

import { colors, typography } from "../../theme";
import type { FeatureMetadataViewModel } from "../../utils/featureFormatting";
import AppCard from "../ui/AppCard";
import FeatureValueRow from "./FeatureValueRow";

type FeatureMetadataCardProps = {
  metadata: FeatureMetadataViewModel;
};

export default function FeatureMetadataCard({ metadata }: FeatureMetadataCardProps) {
  return (
    <AppCard tone="subtle">
      <Text style={styles.title}>Feature Metadata</Text>
      <View style={styles.rows}>
        <FeatureValueRow label="Source" value={metadata.source} />
        <FeatureValueRow label="Created At" value={metadata.createdAt} />
        <FeatureValueRow label="Extractor Version" value={metadata.extractorVersion} />
        <FeatureValueRow label="Window Start" value={metadata.windowStart} />
        <FeatureValueRow label="Window End" value={metadata.windowEnd} />
        <FeatureValueRow label="Source Timezone" value={metadata.sourceTimezone} />
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
