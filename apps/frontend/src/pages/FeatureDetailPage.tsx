import { useCallback, useEffect, useMemo, useState } from "react";
import { useIsFocused } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getFeatureById } from "../api/features";
import { isApiError } from "../api/errors";
import FeatureMetadataCard from "../components/features/FeatureMetadataCard";
import FeatureSectionCard from "../components/features/FeatureSectionCard";
import RawJsonToggle from "../components/features/RawJsonToggle";
import MoodLabelCard from "../components/mood/MoodLabelCard";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppCard from "../components/ui/AppCard";
import AppButton from "../components/ui/AppButton";
import SectionHeader from "../components/ui/SectionHeader";
import { useAppRefreshListener } from "../hooks/useAppRefresh";
import type { RootStackParamList } from "../router/AppRouter";
import { colors, radius, spacing, typography } from "../theme";
import type { FeatureRecord } from "../types/features";
import { buildFeatureSections, extractFeatureMetadata } from "../utils/featureFormatting";

type FeatureDetailPageProps = NativeStackScreenProps<RootStackParamList, "FeatureDetail">;
type DetailViewState = "loading" | "ready" | "not_found" | "error";
type DetailTab = {
  key: string;
  label: string;
  type: "section" | "metadata" | "raw";
  sectionTitle?: string;
};

function toTabKey(label: string): string {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

export default function FeatureDetailPage({ navigation, route }: FeatureDetailPageProps) {
  const { id, refreshAt } = route.params;
  const isFocused = useIsFocused();
  const [feature, setFeature] = useState<FeatureRecord | null>(null);
  const [viewState, setViewState] = useState<DetailViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTabKey, setActiveTabKey] = useState<string | null>(null);
  const [isSectionDropdownOpen, setIsSectionDropdownOpen] = useState(false);

  const loadFeatureDetail = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);
    try {
      const record = await getFeatureById(id);
      setFeature(record);
      setViewState("ready");
    } catch (error) {
      if (isApiError(error) && error.status === 404) {
        setFeature(null);
        setViewState("not_found");
        return;
      }

      const message = error instanceof Error ? error.message : "Failed to load feature detail.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, [id]);

  useEffect(() => {
    void loadFeatureDetail();
  }, [loadFeatureDetail, refreshAt]);

  useAppRefreshListener(() => {
    if (!isFocused) {
      return;
    }
    void loadFeatureDetail();
  });

  const metadata = useMemo(() => (feature ? extractFeatureMetadata(feature) : null), [feature]);
  const sections = useMemo(() => (feature ? buildFeatureSections(feature.data) : []), [feature]);
  const tabs = useMemo<DetailTab[]>(() => {
    const sectionTabs = sections.map((section) => ({
      key: toTabKey(section.title),
      label: section.title,
      type: "section" as const,
      sectionTitle: section.title
    }));

    return [
      ...sectionTabs,
      { key: "metadata", label: "Metadata", type: "metadata" as const },
      { key: "raw-json", label: "Raw JSON", type: "raw" as const }
    ];
  }, [sections]);
  const activeTab = useMemo(() => tabs.find((tab) => tab.key === activeTabKey) ?? tabs[0] ?? null, [tabs, activeTabKey]);

  useEffect(() => {
    if (viewState !== "ready") {
      return;
    }

    if (!tabs.length) {
      setActiveTabKey(null);
      return;
    }

    const preferredTabKey = tabs.find((tab) => tab.type === "section")?.key ?? tabs[0].key;
    const hasActiveTab = activeTabKey ? tabs.some((tab) => tab.key === activeTabKey) : false;

    if (!activeTabKey || !hasActiveTab) {
      setActiveTabKey(preferredTabKey);
    }
  }, [activeTabKey, tabs, viewState]);

  useEffect(() => {
    setActiveTabKey(null);
    setIsSectionDropdownOpen(false);
  }, [id]);

  const handleToggleSectionDropdown = useCallback(() => {
    setIsSectionDropdownOpen((current) => !current);
  }, []);

  const handleSelectTab = useCallback((tabKey: string) => {
    setActiveTabKey(tabKey);
    setIsSectionDropdownOpen(false);
  }, []);

  const handleOpenMoodEditor = useCallback(() => {
    navigation.navigate("FeatureMoodLabel", { id });
  }, [id, navigation]);

  if (viewState === "loading") {
    return <LoadingState message="Loading feature detail..." />;
  }

  if (viewState === "not_found") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Feature Detail" />
        <EmptyState message={`Feature ${id} was not found.`} />
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Feature Detail" />
        <ErrorState message={errorMessage ?? "Failed to load feature detail."} />
        <AppButton label="Try Again" onPress={loadFeatureDetail} style={styles.inlineButton} variant="neutral" />
      </View>
    );
  }

  if (!feature || !metadata) {
    return null;
  }

  return (
    <View style={styles.container}>
      <SectionHeader
        title="Feature Detail"
        subtitle={`Readable breakdown for feature snapshot ${id}.`}
      />
      <MoodLabelCard label={feature.label} />

      <AppCard tone="subtle">
        <Text style={styles.tabHeader}>Feature Sections</Text>
        <Pressable
          accessibilityRole="button"
          onPress={handleToggleSectionDropdown}
          style={styles.dropdownToggle}
          testID="feature-detail-section-dropdown-toggle"
        >
          <Text style={styles.dropdownToggleText}>
            {activeTab ? activeTab.label : "Select a section"}
          </Text>
          <Text style={styles.dropdownToggleChevron}>{isSectionDropdownOpen ? "^" : "v"}</Text>
        </Pressable>
        {isSectionDropdownOpen ? (
          <View style={styles.dropdownMenu} testID="feature-detail-section-dropdown-menu">
            {tabs.map((tab) => {
              const isActive = activeTab?.key === tab.key;
              return (
                <Pressable
                  accessibilityRole="button"
                  key={tab.key}
                  onPress={() => handleSelectTab(tab.key)}
                  style={[styles.dropdownOption, isActive ? styles.dropdownOptionActive : null]}
                  testID={`feature-detail-section-option-${tab.key}`}
                >
                  <Text style={[styles.dropdownOptionText, isActive ? styles.dropdownOptionTextActive : null]}>
                    {tab.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        ) : null}
      </AppCard>

      {activeTab?.type === "metadata" ? <FeatureMetadataCard metadata={metadata} /> : null}
      {activeTab?.type === "raw" ? <RawJsonToggle payload={feature} showToggle={false} /> : null}
      {activeTab?.type === "section" && activeTab.sectionTitle ? (
        <FeatureSectionCard
          rows={sections.find((section) => section.title === activeTab.sectionTitle)?.rows ?? []}
          title={activeTab.label}
        />
      ) : null}

      <AppButton
        label={feature.label ? "Update Mood Label" : "Add Mood Label"}
        onPress={handleOpenMoodEditor}
        style={styles.inlineButton}
        variant="neutral"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm
  },
  inlineButton: {
    alignSelf: "flex-start"
  },
  tabHeader: {
    ...typography.bodyStrong,
    color: colors.textSecondary
  },
  dropdownToggle: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.neutralBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 42,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  dropdownToggleText: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  dropdownToggleChevron: {
    ...typography.helper,
    color: colors.textMuted
  },
  dropdownMenu: {
    borderColor: colors.neutralBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    overflow: "hidden"
  },
  dropdownOption: {
    backgroundColor: colors.surface,
    minHeight: 40,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  dropdownOptionActive: {
    backgroundColor: colors.infoSurface
  },
  dropdownOptionText: {
    ...typography.helper,
    color: colors.textPrimary,
    fontWeight: "700"
  },
  dropdownOptionTextActive: {
    color: colors.primaryStrong
  }
});
