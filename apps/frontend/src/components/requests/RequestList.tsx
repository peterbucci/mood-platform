import { StyleSheet, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import RequestRow from "./RequestRow";

type RequestListProps = {
  onPressFeature?: (featureId: string) => void;
  requests: FeatureRequestRecord[];
};

export default function RequestList({ onPressFeature, requests }: RequestListProps) {
  return (
    <View style={styles.container}>
      {requests.map((request) => (
        <RequestRow key={request.id} onPressFeature={onPressFeature} request={request} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8
  }
});
