import { StyleSheet, View } from "react-native";

import type { FeatureRecord } from "../../types/features";
import { groupFeaturesByDate } from "../../utils/featureHistoryFormatting";
import FeatureDateGroup from "./FeatureDateGroup";
import FeatureHistoryItem from "./FeatureHistoryItem";

type FeatureListProps = {
  features: FeatureRecord[];
  nowMs?: number;
  onPressFeature: (featureId: string) => void;
};

export default function FeatureList({ features, nowMs = Date.now(), onPressFeature }: FeatureListProps) {
  const groups = groupFeaturesByDate(features, nowMs);

  return (
    <View style={styles.listContent}>
      {groups.map((group) => (
        <FeatureDateGroup key={group.key} title={group.title}>
          {group.features.map((feature, index) => (
            <FeatureHistoryItem
              feature={feature}
              key={feature.id}
              nowMs={nowMs}
              onPress={onPressFeature}
              showDivider={index > 0}
            />
          ))}
        </FeatureDateGroup>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  listContent: {
    gap: 16,
    paddingBottom: 4
  }
});
