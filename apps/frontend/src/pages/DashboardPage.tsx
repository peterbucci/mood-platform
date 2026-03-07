import { useCallback, useEffect, useMemo, useState } from "react";
import { useIsFocused, useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getFeatures } from "../api/features";
import CategoryDistributionChart from "../components/dashboard/CategoryDistributionChart";
import InsightCard from "../components/dashboard/InsightCard";
import MetricCard from "../components/dashboard/MetricCard";
import MoodSummaryCard from "../components/dashboard/MoodSummaryCard";
import MoodTrendChart from "../components/dashboard/MoodTrendChart";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import SectionHeader from "../components/ui/SectionHeader";
import { useAppRefreshListener } from "../hooks/useAppRefresh";
import type { RootStackParamList } from "../router/AppRouter";
import { colors, spacing, typography } from "../theme";
import type { FeatureRecord } from "../types/features";
import type { DashboardChartMode, DashboardTimeframe } from "../utils/dashboardAnalytics";
import {
  buildCategoryDistribution,
  buildDashboardInsights,
  buildDashboardMetrics,
  buildDashboardSummary,
  buildMoodTrendChart,
  filterEntriesByTimeframe,
  getDashboardEntries
} from "../utils/dashboardAnalytics";

type DashboardViewState = "loading" | "ready" | "empty" | "error";

const MAX_DASHBOARD_FEATURES = 100;

export default function DashboardPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const isFocused = useIsFocused();
  const [viewState, setViewState] = useState<DashboardViewState>("loading");
  const [chartMode, setChartMode] = useState<DashboardChartMode>("category");
  const [timeframe, setTimeframe] = useState<DashboardTimeframe>(7);
  const [features, setFeatures] = useState<FeatureRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);

    try {
      const records = await getFeatures(MAX_DASHBOARD_FEATURES, 0);
      if (records.length === 0) {
        setFeatures([]);
        setViewState("empty");
        return;
      }

      const sorted = [...records].sort((a, b) => b.createdAt - a.createdAt);
      setFeatures(sorted);
      setViewState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load dashboard data.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  useAppRefreshListener(() => {
    if (!isFocused) {
      return;
    }

    void loadDashboard();
  });

  const entries = useMemo(() => getDashboardEntries(features), [features]);
  const summary = useMemo(() => buildDashboardSummary(entries, Date.now()), [entries]);
  const metrics = useMemo(() => buildDashboardMetrics(entries, Date.now()), [entries]);
  const timeframeEntries = useMemo(() => filterEntriesByTimeframe(entries, timeframe, Date.now()), [entries, timeframe]);
  const chartData = useMemo(
    () => buildMoodTrendChart(timeframeEntries, chartMode, timeframe, Date.now()),
    [chartMode, timeframe, timeframeEntries]
  );
  const distribution = useMemo(() => buildCategoryDistribution(timeframeEntries), [timeframeEntries]);
  const insights = useMemo(() => buildDashboardInsights(entries, Date.now()), [entries]);

  const latestFeature = features[0] ?? null;
  const hasChartData = chartData.series.length > 0 && chartData.points.some((point) => point.total > 0);
  const hasTimeframeData = timeframeEntries.length > 0;

  const handleOpenLatestFeature = useCallback(() => {
    if (!latestFeature) {
      return;
    }

    navigation.navigate("FeatureDetail", { id: latestFeature.id });
  }, [latestFeature, navigation]);

  if (viewState === "loading") {
    return <LoadingState message="Loading dashboard overview..." />;
  }

  if (viewState === "empty") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Dashboard" subtitle="Quick health overview from your recent mood labels." />
        <EmptyState message="No feature data available yet. Log an emotion to build your dashboard trend." />
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Dashboard" />
        <ErrorState message={errorMessage ?? "Failed to load dashboard data."} />
        <AppButton label="Try Again" onPress={loadDashboard} style={styles.inlineButton} variant="neutral" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionHeader title="Dashboard" subtitle="Quick health overview from your recent mood labels." />

      <MoodSummaryCard
        category={summary.primaryEntry?.category ?? null}
        emotion={summary.primaryEntry?.emotionLabel ?? null}
        entriesToday={summary.entriesToday}
        isToday={summary.isToday}
        lastLogged={summary.lastLogged}
        message={summary.message}
      />

      {entries.length > 0 ? (
        <View style={styles.metricsGrid}>
          {metrics.map((metric) => (
            <View key={metric.key} style={styles.metricCell}>
              <MetricCard
                detail={metric.detail}
                icon={metric.icon}
                label={metric.label}
                tone={metric.tone}
                value={metric.value}
              />
            </View>
          ))}
        </View>
      ) : null}

      {entries.length === 0 ? (
        <EmptyState message="No mood labels yet. Add labels on feature detail pages to populate this dashboard." />
      ) : (
        <>
          {hasChartData ? (
            <MoodTrendChart
              mode={chartMode}
              onChangeMode={setChartMode}
              onChangeTimeframe={setTimeframe}
              points={chartData.points}
              series={chartData.series}
              timeframe={timeframe}
            />
          ) : (
            <EmptyState message="No mood labels in the selected timeframe yet. Try a wider range or log a new mood." />
          )}

          {hasTimeframeData ? (
            <CategoryDistributionChart distribution={distribution} timeframe={timeframe} />
          ) : null}

          <InsightCard insights={insights} />
        </>
      )}

      {latestFeature ? (
        <Pressable
          accessibilityRole="button"
          onPress={handleOpenLatestFeature}
          style={styles.latestFeatureLink}
          testID="dashboard-latest-feature-link"
        >
          <Text style={styles.latestFeatureLinkText}>View details for the latest feature set</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 164
  },
  latestFeatureLink: {
    alignSelf: "flex-start",
    paddingVertical: spacing.xs
  },
  latestFeatureLinkText: {
    ...typography.bodyStrong,
    color: colors.primaryStrong,
    textDecorationLine: "underline"
  },
  metricCell: {
    width: "48%"
  },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between"
  }
});
