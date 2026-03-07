import { StyleSheet } from "react-native";

import { colors } from "../../theme";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type EmptyStateProps = {
  message: string;
};

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <AppCard style={styles.container}>
      <InfoText tone="muted">{message}</InfoText>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  container: {
    borderColor: colors.borderStrong,
    borderStyle: "dashed"
  }
});
