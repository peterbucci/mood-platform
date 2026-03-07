import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

export default function EmptyRequestsState() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>No recent captures yet</Text>
      <Text style={styles.subtitle}>
        Log how you feel and capture a new feature snapshot. Your recent activity will show up here.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.xxs,
    minHeight: 88,
    justifyContent: "center"
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
