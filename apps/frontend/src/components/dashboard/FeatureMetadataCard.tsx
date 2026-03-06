import { StyleSheet, Text, View } from "react-native";

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
    <View style={styles.card}>
      <Text style={styles.title}>Snapshot Metadata</Text>
      <View style={styles.rows}>
        <FeatureValueRow label="Created At" value={metadata.createdAt} />
        <FeatureValueRow label="Source" value={metadata.source} />
        <FeatureValueRow label="Extractor Version" value={metadata.extractorVersion} />
        <FeatureValueRow label="Window Start" value={metadata.windowStart} />
        <FeatureValueRow label="Window End" value={metadata.windowEnd} />
        <FeatureValueRow label="Source Timezone" value={metadata.sourceTimezone} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#f8fafc",
    borderColor: "#cbd5e1",
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
    padding: 14
  },
  title: {
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "700"
  },
  rows: {
    gap: 7
  }
});
