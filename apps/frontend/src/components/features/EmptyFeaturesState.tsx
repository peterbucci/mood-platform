import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

export default function EmptyFeaturesState() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>No feature captures yet</Text>
      <Text style={styles.subtitle}>Log an emotion to generate your first capture.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.xxs,
    justifyContent: "center",
    minHeight: 96
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
