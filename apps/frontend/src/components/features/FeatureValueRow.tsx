import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

type FeatureValueRowProps = {
  label: string;
  showDivider?: boolean;
  value: string;
};

export default function FeatureValueRow({ label, showDivider = false, value }: FeatureValueRowProps) {
  return (
    <View style={[styles.row, showDivider ? styles.rowDivider : null]}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    ...typography.body,
    color: colors.textSecondary,
    flex: 1,
    paddingRight: spacing.md
  },
  row: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between",
    paddingVertical: spacing.sm
  },
  rowDivider: {
    borderTopColor: colors.border,
    borderTopWidth: 1
  },
  value: {
    ...typography.bodyStrong,
    color: colors.textPrimary,
    flex: 1,
    textAlign: "right"
  }
});
