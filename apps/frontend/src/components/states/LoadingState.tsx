import { ActivityIndicator, StyleSheet, View } from "react-native";

import { colors, spacing } from "../../theme";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type LoadingStateProps = {
  message?: string;
};

export default function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <AppCard>
      <View style={styles.container}>
        <ActivityIndicator size="small" color={colors.primary} />
        <InfoText>{message}</InfoText>
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "center",
    minHeight: 56
  }
});
