import { StyleSheet, View } from "react-native";

import type { FeatureRecord } from "../../types/features";
import FeatureRow from "./FeatureRow";

type FeatureListProps = {
  features: FeatureRecord[];
  onPressFeature: (featureId: string) => void;
};

export default function FeatureList({ features, onPressFeature }: FeatureListProps) {
  return (
    <View style={styles.listContent}>
      {features.map((feature) => (
        <FeatureRow key={feature.id} feature={feature} onPress={onPressFeature} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  listContent: {
    gap: 8,
    paddingBottom: 12
  }
});
