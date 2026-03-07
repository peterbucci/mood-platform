import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

type SettingsSectionHeaderProps = {
  subtitle?: string;
  title: string;
};

export default function SettingsSectionHeader({
  subtitle,
  title
}: SettingsSectionHeaderProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.xxs
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  }
});
