import { useCallback, useEffect, useMemo, useState } from "react";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { StyleSheet, Text, View } from "react-native";

import { getFeatureById } from "../api/features";
import { isApiError } from "../api/errors";
import FeatureKeyMetricsCard from "../components/features/FeatureKeyMetricsCard";
import FeatureMetadataCard from "../components/features/FeatureMetadataCard";
import FeatureSectionCard from "../components/features/FeatureSectionCard";
import FeatureSectionTabs from "../components/features/FeatureSectionTabs";
import FeatureSnapshotSummaryCard from "../components/features/FeatureSnapshotSummaryCard";
import RawJsonToggle from "../components/features/RawJsonToggle";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import AppCard from "../components/ui/AppCard";
import InfoText from "../components/ui/InfoText";
import SectionHeader from "../components/ui/SectionHeader";
import type { RootStackParamList } from "../router/AppRouter";
import { colors, radius, spacing, typography } from "../theme";
import type { FeatureRecord } from "../types/features";
import { formatFeatureRelativeTime } from "../utils/featureHistoryFormatting";
import {
  buildFeatureSections,
  buildFeatureSnapshotContextLine,
  extractFeatureKeyMetrics,
  extractFeatureMetadata,
  getFeatureSectionDescription
} from "../utils/featureFormatting";

type FeatureDetailPageProps = NativeStackScreenProps<RootStackParamList, "FeatureDetail">;
type DetailViewState = "loading" | "ready" | "not_found" | "error";

function toTabKey(label: string): string {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

export default function FeatureDetailPage({ navigation, route }: FeatureDetailPageProps) {
  const { id, refreshAt } = route.params;
  const [feature, setFeature] = useState<FeatureRecord | null>(null);
  const [viewState, setViewState] = useState<DetailViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeSectionKey, setActiveSectionKey] = useState<string | null>(null);

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

  const metadata = useMemo(() => (feature ? extractFeatureMetadata(feature) : null), [feature]);
  const sections = useMemo(() => (feature ? buildFeatureSections(feature.data) : []), [feature]);
  const keyMetrics = useMemo(() => (feature ? extractFeatureKeyMetrics(feature.data) : []), [feature]);
  const tabs = useMemo(
    () =>
      sections.map((section) => ({
        key: toTabKey(section.title),
        label: section.title
      })),
    [sections]
  );
  const activeSection = useMemo(
    () => sections.find((section) => toTabKey(section.title) === activeSectionKey) ?? sections[0] ?? null,
    [activeSectionKey, sections]
  );

  useEffect(() => {
    if (viewState !== "ready") {
      return;
    }

    const preferredKey = tabs[0]?.key ?? null;
    if (!preferredKey) {
      setActiveSectionKey(null);
      return;
    }

    const hasActiveSection = activeSectionKey ? tabs.some((tab) => tab.key === activeSectionKey) : false;
    if (!activeSectionKey || !hasActiveSection) {
      setActiveSectionKey(preferredKey);
    }
  }, [activeSectionKey, tabs, viewState]);

  useEffect(() => {
    setActiveSectionKey(null);
  }, [id]);

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

  const relativeTime = formatFeatureRelativeTime(feature.createdAt);

  return (
    <View style={styles.container}>
      <View style={styles.pageHeader}>
        <View style={styles.pageHeaderCopy}>
          <Text style={styles.pageTitle}>Feature Detail</Text>
          <Text style={styles.pageSubtitle}>
            Summary first, then a readable breakdown of the signals captured in this snapshot.
          </Text>
        </View>
        <Text style={styles.headerTime}>{relativeTime}</Text>
      </View>

      <View style={styles.headerMetaRow}>
        <View style={styles.headerMetaItem}>
          <Text style={styles.headerMetaLabel}>Feature ID</Text>
          <Text style={styles.headerMetaValue}>{feature.id}</Text>
        </View>
      </View>

      <FeatureSnapshotSummaryCard
        capturedAt={metadata.createdAt}
        capturedRelative={relativeTime}
        contextLine={buildFeatureSnapshotContextLine(feature.source)}
        label={feature.label}
        moodActionLabel={feature.label ? "Update Mood Label" : "Add Mood Label"}
        onPressMoodAction={handleOpenMoodEditor}
        sourceLabel={metadata.source}
      />

      <FeatureKeyMetricsCard metrics={keyMetrics} />

      {sections.length > 0 ? (
        <>
          <AppCard style={styles.sectionPickerCard} tone="subtle">
            <View style={styles.sectionPickerHeader}>
              <Text style={styles.sectionPickerTitle}>Detailed Sections</Text>
              <InfoText tone="helper">Choose a section to explore more values.</InfoText>
            </View>
            <FeatureSectionTabs activeKey={activeSectionKey} onSelectTab={setActiveSectionKey} tabs={tabs} />
          </AppCard>

          {activeSection ? (
            <FeatureSectionCard
              rows={activeSection.rows}
              subtitle={getFeatureSectionDescription(activeSection.title)}
              title={activeSection.title}
            />
          ) : null}
        </>
      ) : (
        <AppCard tone="subtle">
          <Text style={styles.emptySectionTitle}>Detailed sections are not available for this snapshot yet.</Text>
        </AppCard>
      )}

      <FeatureMetadataCard metadata={metadata} />
      <RawJsonToggle payload={feature} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg
  },
  emptySectionTitle: {
    ...typography.bodyStrong,
    color: colors.textSecondary
  },
  headerMetaItem: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flex: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  headerMetaLabel: {
    ...typography.helper,
    color: colors.textMuted,
    fontWeight: "700"
  },
  headerMetaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    width: "100%"
  },
  headerMetaValue: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  headerTime: {
    ...typography.helper,
    color: colors.textMuted,
    textAlign: "right"
  },
  inlineButton: {
    alignSelf: "flex-start"
  },
  pageHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  pageHeaderCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  pageSubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  pageTitle: {
    ...typography.title,
    color: colors.textPrimary
  },
  sectionPickerCard: {
    gap: spacing.md
  },
  sectionPickerHeader: {
    gap: spacing.xxs
  },
  sectionPickerTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
