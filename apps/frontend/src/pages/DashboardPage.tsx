import { useCallback, useEffect, useMemo, useState } from "react";
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
import { colors, radius, spacing, typography } from "../theme";
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
  const [viewState, setViewState] = useState<DashboardViewState>("loading");
  const [chartMode, setChartMode] = useState<DashboardChartMode>("category");
  const [timeframe, setTimeframe] = useState<DashboardTimeframe>(7);
  const [features, setFeatures] = useState<FeatureRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadDashboard = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "initial") {
      setViewState("loading");
    } else {
      setIsRefreshing(true);
    }

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
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard("initial");
  }, [loadDashboard]);

  const entries = useMemo(() => getDashboardEntries(features), [features]);
  const summary = useMemo(() => buildDashboardSummary(entries, Date.now()), [entries]);
  const metrics = useMemo(() => buildDashboardMetrics(entries, Date.now()), [entries]);
  const timeframeEntries = useMemo(
    () => filterEntriesByTimeframe(entries, timeframe, Date.now()),
    [entries, timeframe]
  );
  const chartData = useMemo(
    () => buildMoodTrendChart(timeframeEntries, chartMode, timeframe, Date.now()),
    [chartMode, timeframe, timeframeEntries]
  );
  const distribution = useMemo(() => buildCategoryDistribution(timeframeEntries), [timeframeEntries]);
  const insights = useMemo(() => buildDashboardInsights(entries, Date.now()), [entries]);

  const hasChartData = chartData.series.length > 0 && chartData.points.some((point) => point.total > 0);
  const hasTimeframeData = timeframeEntries.length > 0;

  const refreshMode = features.length > 0 ? "refresh" : "initial";

  if (viewState === "loading") {
    return <LoadingState message="Loading dashboard overview..." />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.pageHeader}>
        <View style={styles.pageHeaderCopy}>
          <Text style={styles.pageTitle}>Dashboard</Text>
          <Text style={styles.pageSubtitle}>Quick health overview from your recent mood labels.</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          disabled={isRefreshing}
          onPress={() => void loadDashboard(refreshMode)}
          style={[styles.refreshButton, isRefreshing ? styles.refreshButtonDisabled : null]}
          testID="dashboard-refresh-button"
        >
          <Text style={styles.refreshButtonText}>{isRefreshing ? "Refreshing..." : "Refresh"}</Text>
        </Pressable>
      </View>

      {viewState === "empty" ? (
        <EmptyState message="No feature data available yet. Log an emotion to build your dashboard trend." />
      ) : null}

      {viewState === "error" ? (
        <>
          <ErrorState message={errorMessage ?? "Failed to load dashboard data."} />
          <AppButton
            label="Try Again"
            onPress={() => void loadDashboard(refreshMode)}
            style={styles.inlineButton}
            variant="neutral"
          />
        </>
      ) : null}

      {viewState === "ready" ? (
        <>
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
        </>
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
  metricCell: {
    width: "48%"
  },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between"
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
  }
});
