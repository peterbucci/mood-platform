import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type FeatureSectionTab = {
  key: string;
  label: string;
};

type FeatureSectionTabsProps = {
  activeKey: string | null;
  onSelectTab: (key: string) => void;
  tabs: FeatureSectionTab[];
};

export default function FeatureSectionTabs({
  activeKey,
  onSelectTab,
  tabs
}: FeatureSectionTabsProps) {
  return (
    <View style={styles.tabs} testID="feature-detail-section-tabs">
      {tabs.map((tab) => {
        const isActive = tab.key === activeKey;
        return (
          <Pressable
            accessibilityRole="button"
            key={tab.key}
            onPress={() => onSelectTab(tab.key)}
            style={({ pressed }) => [
              styles.tab,
              isActive ? styles.tabActive : null,
              pressed ? styles.tabPressed : null
            ]}
            testID={`feature-detail-section-tab-${tab.key}`}
          >
            <Text style={[styles.tabText, isActive ? styles.tabTextActive : null]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  tab: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 36,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  tabActive: {
    backgroundColor: colors.infoSurface,
    borderColor: colors.infoBorder
  },
  tabPressed: {
    opacity: 0.75
  },
  tabText: {
    ...typography.helper,
    color: colors.textSecondary,
    fontWeight: "700"
  },
  tabTextActive: {
    color: colors.primaryStrong
  },
  tabs: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  }
});
