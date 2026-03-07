import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getFeatures } from "../api/features";
import EmptyFeaturesState from "../components/features/EmptyFeaturesState";
import FeatureList from "../components/features/FeatureList";
import FeatureSummaryCard from "../components/features/FeatureSummaryCard";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import AppCard from "../components/ui/AppCard";
import InfoText from "../components/ui/InfoText";
import type { RootStackParamList } from "../router/AppRouter";
import { colors, radius, spacing, typography } from "../theme";
import type { FeatureRecord } from "../types/features";
import {
  formatFeatureRelativeTime,
  getMostCommonRecentCategory,
  sortFeaturesByNewest
} from "../utils/featureHistoryFormatting";
import { getMoodDisplayModel } from "../utils/moodFormatting";

type SummaryTone = "neutral" | "info" | "energized" | "calm" | "stressed" | "tired";

function pluralizeCapture(count: number): string {
  return count === 1 ? "capture" : "captures";
}

function getSummaryTone(category: string | null | undefined): SummaryTone {
  const normalized = category?.toLowerCase();
  if (normalized === "energized") {
    return "energized";
  }
  if (normalized === "calm") {
    return "calm";
  }
  if (normalized === "stressed") {
    return "stressed";
  }
  if (normalized === "tired") {
    return "tired";
  }

  return "neutral";
}

export default function FeaturesPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [features, setFeatures] = useState<FeatureRecord[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadFeatures = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "initial") {
      setIsInitialLoading(true);
    } else {
      setIsRefreshing(true);
    }

    try {
      const records = await getFeatures();
      setFeatures(sortFeaturesByNewest(records));
      setErrorMessage(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load feature history.";
      setErrorMessage(message);
    } finally {
      setIsInitialLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadFeatures("initial");
  }, [loadFeatures]);

  const handleOpenFeature = useCallback(
    (featureId: string) => {
      navigation.navigate("FeatureDetail", { id: featureId });
    },
    [navigation]
  );

  const nowMs = Date.now();
  const latestFeature = features[0] ?? null;
  const recentCategory = useMemo(() => getMostCommonRecentCategory(features), [features]);
  const latestMoodSummary = latestFeature
    ? getMoodDisplayModel(latestFeature.label).text
    : "Your next capture will appear here.";
  const historyStatusText = features.length
    ? `${features.length} ${pluralizeCapture(features.length)}`
    : errorMessage
      ? "Unavailable"
      : "Ready when you are";
  const totalCapturesValue = isInitialLoading && !features.length ? "--" : String(features.length);
  const lastCaptureValue =
    isInitialLoading && !features.length
      ? "Loading"
      : latestFeature
        ? formatFeatureRelativeTime(latestFeature.createdAt, nowMs)
        : "No captures";
  const recentCategoryValue = isInitialLoading && !features.length ? "Loading" : recentCategory.label;
  const recentCategoryTone = recentCategory.category ? getSummaryTone(recentCategory.category) : "neutral";

  return (
    <View style={styles.container}>
      <View style={styles.pageHeader}>
        <View style={styles.pageHeaderCopy}>
          <Text style={styles.pageTitle}>Features</Text>
          <Text style={styles.pageSubtitle}>
            Review recent capture history and open any snapshot for a full breakdown.
          </Text>
        </View>
        <Pressable
          accessibilityRole="button"
          disabled={isRefreshing || isInitialLoading}
          onPress={() => void loadFeatures(features.length > 0 ? "refresh" : "initial")}
          style={[styles.refreshButton, isRefreshing || isInitialLoading ? styles.refreshButtonDisabled : null]}
          testID="features-refresh-button"
        >
          <Text style={styles.refreshButtonText}>{isRefreshing ? "Refreshing..." : "Refresh"}</Text>
        </Pressable>
      </View>

      <View style={styles.summaryGrid}>
        <View style={styles.summaryHalf}>
          <FeatureSummaryCard
            detail={
              features.length > 0
                ? "Across your recent capture history"
                : "History builds as you capture more snapshots"
            }
            label="Total captures"
            value={totalCapturesValue}
          />
        </View>
        <View style={styles.summaryHalf}>
          <FeatureSummaryCard
            detail={latestMoodSummary}
            label="Last capture"
            tone={latestFeature ? getSummaryTone(latestFeature.label?.category) : "info"}
            value={lastCaptureValue}
          />
        </View>
        <View style={styles.summaryFull}>
          <FeatureSummaryCard
            detail={recentCategory.detail}
            label="Recent category"
            tone={recentCategoryTone}
            value={recentCategoryValue}
          />
        </View>
      </View>

      {isInitialLoading && !features.length ? (
        <LoadingState message="Loading feature history..." />
      ) : (
        <AppCard style={styles.historyCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionHeaderCopy}>
              <Text style={styles.sectionTitle}>Capture history</Text>
              <Text style={styles.sectionSubtitle}>
                Browse recent snapshots, spot patterns, and tap any entry for more detail.
              </Text>
            </View>
            <Text style={styles.sectionStatus}>{historyStatusText}</Text>
          </View>

          {!features.length && errorMessage ? (
            <View style={styles.inlineState}>
              <Text style={styles.errorTitle}>Unable to load feature history</Text>
              <InfoText tone="danger">{errorMessage}</InfoText>
              <AppButton
                label="Try Again"
                onPress={() => void loadFeatures("initial")}
                style={styles.inlineButton}
                variant="neutral"
              />
            </View>
          ) : null}

          {!features.length && !errorMessage ? <EmptyFeaturesState /> : null}

          {features.length > 0 ? (
            <>
              {errorMessage ? (
                <InfoText tone="warning">Showing your latest capture history. Refresh to try again.</InfoText>
              ) : null}
              <FeatureList features={features} nowMs={nowMs} onPressFeature={handleOpenFeature} />
            </>
          ) : null}
        </AppCard>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg
  },
  errorTitle: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  historyCard: {
    gap: spacing.md
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 128
  },
  inlineState: {
    gap: spacing.xs,
    justifyContent: "center",
    minHeight: 112
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
  refreshButton: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  refreshButtonDisabled: {
    opacity: 0.6
  },
  refreshButtonText: {
    ...typography.helper,
    color: colors.textPrimary,
    fontWeight: "700"
  },
  sectionHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  sectionHeaderCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  sectionStatus: {
    ...typography.helper,
    color: colors.textMuted,
    textAlign: "right"
  },
  sectionSubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  sectionTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  summaryFull: {
    width: "100%"
  },
  summaryGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  summaryHalf: {
    width: "48%"
  }
});
