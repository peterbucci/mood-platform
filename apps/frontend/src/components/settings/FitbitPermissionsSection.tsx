import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import { formatFitbitPermission, formatFitbitPermissionsPreview } from "../../utils/fitbitConnectionFormatting";

type FitbitPermissionsSectionProps = {
  scopes: string[];
};

export default function FitbitPermissionsSection({ scopes }: FitbitPermissionsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const permissionLabels = useMemo(
    () => Array.from(new Set(scopes.map(formatFitbitPermission))),
    [scopes]
  );

  if (!permissionLabels.length) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Pressable
        accessibilityRole="button"
        onPress={() => setIsExpanded((current) => !current)}
        style={styles.header}
        testID="fitbit-permissions-toggle"
      >
        <View style={styles.headerCopy}>
          <Text style={styles.title}>Permissions</Text>
          <Text style={styles.preview}>{formatFitbitPermissionsPreview(scopes)}</Text>
        </View>
        <Text style={styles.actionLabel}>{isExpanded ? "Hide" : "View all"}</Text>
      </Pressable>

      {isExpanded ? (
        <View style={styles.chipWrap}>
          {permissionLabels.map((label) => (
            <View key={label} style={styles.chip}>
              <Text style={styles.chipText}>{label}</Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  actionLabel: {
    ...typography.helper,
    color: colors.primaryStrong,
    fontWeight: "700"
  },
  chip: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs
  },
  chipText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs
  },
  container: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md
  },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  headerCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  preview: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
