import { StyleSheet, Text, View } from "react-native";

import type { RequestStatus } from "../../types/requests";

type StatusBadgeProps = {
  status: RequestStatus;
};

function getLabel(status: RequestStatus): string {
  if (status === "fulfilled") {
    return "Fulfilled";
  }
  if (status === "canceled") {
    return "Canceled";
  }
  return "Pending";
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const isFulfilled = status === "fulfilled";
  const isCanceled = status === "canceled";
  return (
    <View
      style={[
        styles.badge,
        isFulfilled ? styles.fulfilledBadge : null,
        isCanceled ? styles.canceledBadge : null
      ]}
    >
      <Text
        style={[
          styles.label,
          isFulfilled ? styles.fulfilledLabel : null,
          isCanceled ? styles.canceledLabel : null
        ]}
      >
        {getLabel(status)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "#ffedd5",
    borderColor: "#fdba74",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4
  },
  fulfilledBadge: {
    backgroundColor: "#ecfdf5",
    borderColor: "#86efac"
  },
  canceledBadge: {
    backgroundColor: "#f3f4f6",
    borderColor: "#d1d5db"
  },
  label: {
    color: "#9a3412",
    fontSize: 12,
    fontWeight: "700"
  },
  fulfilledLabel: {
    color: "#065f46"
  },
  canceledLabel: {
    color: "#4b5563"
  }
});
