import { StyleSheet, Text } from "react-native";

import { colors, typography } from "../../theme";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type PendingCountCardProps = {
  pendingCount: number;
};

export default function PendingCountCard({ pendingCount }: PendingCountCardProps) {
  return (
    <AppCard tone="info">
      <InfoText tone="helper">Pending Requests</InfoText>
      <Text style={styles.value} testID="pending-count-value">
        {pendingCount}
      </Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  value: {
    ...typography.title,
    color: colors.primaryStrong,
    fontSize: 28,
    fontWeight: "800"
  }
});
