import { StyleSheet, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import RequestListItem from "./RequestListItem";

type RequestListProps = {
  cancelErrorById?: Record<string, string>;
  cancelingById?: Record<string, boolean>;
  onPressCancel?: (requestId: string) => void;
  onPressFeature?: (featureId: string) => void;
  requests: FeatureRequestRecord[];
};

export default function RequestList({
  cancelErrorById,
  cancelingById,
  onPressCancel,
  onPressFeature,
  requests
}: RequestListProps) {
  return (
    <View style={styles.container}>
      {requests.map((request, index) => (
        <RequestListItem
          key={request.id}
          cancelError={cancelErrorById?.[request.id]}
          isCanceling={Boolean(cancelingById?.[request.id])}
          onPressCancel={onPressCancel}
          onPressFeature={onPressFeature}
          request={request}
          showDivider={index > 0}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 0
  }
});
