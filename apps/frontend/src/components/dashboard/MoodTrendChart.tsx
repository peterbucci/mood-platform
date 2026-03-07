import { useCallback, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { LayoutChangeEvent } from "react-native";
import { VictoryArea, VictoryAxis, VictoryChart, VictoryStack, VictoryTheme } from "victory-native";

import { colors, radius, spacing, typography } from "../../theme";
import type {
  DashboardChartMode,
  DashboardChartPoint,
  DashboardChartSeries,
  DashboardTimeframe
} from "../../utils/dashboardAnalytics";
import AppCard from "../ui/AppCard";
import { getDashboardCategoryTheme, getDashboardEmotionColor } from "./dashboardTheme";

const CHART_HEIGHT = 220;
const CHART_MIN_WIDTH = 280;
const CHART_DEFAULT_WIDTH = 340;
const TIMEFRAMES: DashboardTimeframe[] = [7, 14, 30];

type MoodTrendChartProps = {
  mode: DashboardChartMode;
  onChangeMode: (mode: DashboardChartMode) => void;
  onChangeTimeframe: (timeframe: DashboardTimeframe) => void;
  points: DashboardChartPoint[];
  series: DashboardChartSeries[];
  timeframe: DashboardTimeframe;
};

function buildTickValues(pointCount: number): number[] {
  if (pointCount <= 7) {
    return Array.from({ length: pointCount }, (_, index) => index + 1).filter((value) => value % 2 === 1 || value === pointCount);
  }
  if (pointCount <= 14) {
    return Array.from({ length: pointCount }, (_, index) => index + 1).filter(
      (value) => value === 1 || value === pointCount || value % 4 === 0
    );
  }

  return Array.from({ length: pointCount }, (_, index) => index + 1).filter(
    (value) => value === 1 || value === pointCount || value % 7 === 0
  );
}

function resolveSeriesColor(series: DashboardChartSeries): string {
  if (!series.category) {
    return colors.borderStrong;
  }

  if (series.key === series.category) {
    return getDashboardCategoryTheme(series.category).line;
  }

  return getDashboardEmotionColor(series.category, series.label);
}

export default function MoodTrendChart({
  mode,
  onChangeMode,
  onChangeTimeframe,
  points,
  series,
  timeframe
}: MoodTrendChartProps) {
  const [chartWidth, setChartWidth] = useState(CHART_DEFAULT_WIDTH);
  const maxTotal = Math.max(...points.map((point) => point.total), 1);

  const tickValues = useMemo(() => buildTickValues(points.length), [points.length]);
  const tickLabels = useMemo(() => {
    return new Map(points.map((point, index) => [index + 1, point.label]));
  }, [points]);
  const resolvedSeries = useMemo(
    () =>
      series.map((seriesItem) => ({
        ...seriesItem,
        color: resolveSeriesColor(seriesItem),
        data: points.map((point, index) => ({
          x: index + 1,
          y: point.values[seriesItem.key] ?? 0
        }))
      })),
    [points, series]
  );

  const handleLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const nextWidth = Math.max(CHART_MIN_WIDTH, Math.floor(event.nativeEvent.layout.width));
      if (nextWidth !== chartWidth) {
        setChartWidth(nextWidth);
      }
    },
    [chartWidth]
  );

  return (
    <AppCard style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.title}>Mood Trend</Text>
          <Text style={styles.subtitle}>Daily stacked trend for the last {timeframe} days.</Text>
        </View>
        <View style={styles.segmentRow}>
          {TIMEFRAMES.map((option) => {
            const isActive = timeframe === option;
            return (
              <Pressable
                accessibilityRole="button"
                key={option}
                onPress={() => onChangeTimeframe(option)}
                style={[styles.segmentButton, isActive ? styles.segmentButtonActive : null]}
                testID={`dashboard-timeframe-${option}`}
              >
                <Text style={[styles.segmentText, isActive ? styles.segmentTextActive : null]}>{option}D</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.modeRow}>
        <Pressable
          accessibilityRole="button"
          onPress={() => onChangeMode("category")}
          style={[styles.modeButton, mode === "category" ? styles.modeButtonActive : null]}
          testID="dashboard-mode-category"
        >
          <Text style={[styles.modeButtonText, mode === "category" ? styles.modeButtonTextActive : null]}>
            Categories
          </Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => onChangeMode("emotion")}
          style={[styles.modeButton, mode === "emotion" ? styles.modeButtonActive : null]}
          testID="dashboard-mode-emotion"
        >
          <Text style={[styles.modeButtonText, mode === "emotion" ? styles.modeButtonTextActive : null]}>
            Emotions
          </Text>
        </Pressable>
      </View>

      <View style={styles.plotArea} onLayout={handleLayout} testID="mood-history-chart">
        <VictoryChart
          domain={{ y: [0, maxTotal] }}
          height={CHART_HEIGHT}
          padding={{ bottom: 36, left: 42, right: 20, top: 18 }}
          theme={VictoryTheme.material}
          width={chartWidth}
        >
          <VictoryAxis
            fixLabelOverlap
            style={{
              axis: { stroke: colors.borderStrong, strokeWidth: 1 },
              grid: { stroke: "transparent" },
              tickLabels: {
                fill: colors.textMuted,
                fontSize: 10,
                padding: 8
              },
              ticks: { stroke: "transparent" }
            }}
            tickFormat={(value: number) => tickLabels.get(value) ?? ""}
            tickValues={tickValues}
          />
          <VictoryAxis
            dependentAxis
            style={{
              axis: { stroke: colors.borderStrong, strokeWidth: 1 },
              grid: {
                stroke: colors.border,
                strokeDasharray: "4, 6",
                strokeWidth: 0.9
              },
              tickLabels: {
                fill: colors.textMuted,
                fontSize: 10,
                padding: 6
              },
              ticks: { stroke: "transparent" }
            }}
            tickCount={4}
          />
          <VictoryStack>
            {resolvedSeries.map((seriesItem) => (
              <VictoryArea
                data={seriesItem.data}
                interpolation="monotoneX"
                key={seriesItem.key}
                style={{
                  data: {
                    fill: seriesItem.color,
                    fillOpacity: 0.24,
                    stroke: seriesItem.color,
                    strokeWidth: 1.4
                  }
                }}
              />
            ))}
          </VictoryStack>
        </VictoryChart>
      </View>

      <View style={styles.legend}>
        {resolvedSeries.map((seriesItem) => (
          <View key={seriesItem.key} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: seriesItem.color }]} />
            <Text numberOfLines={1} style={styles.legendLabel}>
              {seriesItem.label}
            </Text>
          </View>
        ))}
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  headerRow: {
    gap: spacing.md
  },
  legend: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  legendDot: {
    borderRadius: radius.pill,
    height: 10,
    width: 10
  },
  legendItem: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  legendLabel: {
    ...typography.helper,
    color: colors.textSecondary,
    maxWidth: 110
  },
  modeButton: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  modeButtonActive: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary
  },
  modeButtonText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  modeButtonTextActive: {
    color: colors.inverseText
  },
  modeRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  plotArea: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    minHeight: CHART_HEIGHT,
    overflow: "hidden",
    width: "100%"
  },
  segmentButton: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 34,
    minWidth: 44,
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs
  },
  segmentButtonActive: {
    backgroundColor: colors.infoSurface,
    borderColor: colors.infoBorder
  },
  segmentRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs
  },
  segmentText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  segmentTextActive: {
    color: colors.primaryStrong
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  titleBlock: {
    flex: 1,
    gap: spacing.xxs
  }
});
