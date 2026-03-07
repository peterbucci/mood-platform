import { StyleSheet, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import RequestListItem from "./RequestListItem";

type RequestListProps = {
  deleteErrorById?: Record<string, string>;
  deletingById?: Record<string, boolean>;
  onPressDelete?: (requestId: string) => void;
  onPressFeature?: (featureId: string) => void;
  requests: FeatureRequestRecord[];
};

export default function RequestList({
  deleteErrorById,
  deletingById,
  onPressDelete,
  onPressFeature,
  requests
}: RequestListProps) {
  return (
    <View style={styles.container}>
      {requests.map((request, index) => (
        <RequestListItem
          key={request.id}
          deleteError={deleteErrorById?.[request.id]}
          isDeleting={Boolean(deletingById?.[request.id])}
          onPressDelete={onPressDelete}
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
