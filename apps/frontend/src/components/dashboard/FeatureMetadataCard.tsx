import { StyleSheet, Text, View } from "react-native";

import { colors, typography } from "../../theme";
import AppCard from "../ui/AppCard";
import FeatureValueRow from "./FeatureValueRow";

type FeatureMetadata = {
  createdAt: string;
  source: string;
  extractorVersion: string;
  windowStart: string;
  windowEnd: string;
  sourceTimezone: string;
};

type FeatureMetadataCardProps = {
  metadata: FeatureMetadata;
};

export default function FeatureMetadataCard({ metadata }: FeatureMetadataCardProps) {
  return (
    <AppCard tone="subtle">
      <Text style={styles.title}>Snapshot Metadata</Text>
      <View style={styles.rows}>
        <FeatureValueRow label="Created At" value={metadata.createdAt} />
        <FeatureValueRow label="Source" value={metadata.source} />
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
