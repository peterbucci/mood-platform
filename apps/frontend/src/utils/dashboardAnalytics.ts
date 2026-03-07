import type { MoodCategory } from "../types/mood";
import type { FeatureRecord } from "../types/features";
import { formatMoodCategory } from "./moodFormatting";
import { isMoodCategory } from "./moodTaxonomy";

export type DashboardChartMode = "category" | "emotion";
export type DashboardTimeframe = 7 | 14 | 30;
export type MetricTone = MoodCategory | "neutral" | "primary";

export type DashboardEntry = {
  category: MoodCategory;
  createdAt: number;
  dayKey: string;
  dayLabel: string;
  dayStartMs: number;
  emotionKey: string;
  emotionLabel: string;
  id: string;
  isWeekend: boolean;
};

export type DashboardChartSeries = {
  category?: MoodCategory;
  key: string;
  label: string;
};

export type DashboardChartPoint = {
  key: string;
  label: string;
  total: number;
  values: Record<string, number>;
};

export type DashboardSummary = {
  entriesToday: number;
  isToday: boolean;
  lastLogged: string;
  message: string;
  primaryEntry: DashboardEntry | null;
};

export type DashboardMetric = {
  detail: string;
  icon: string;
  key: string;
  label: string;
  tone: MetricTone;
  value: string;
};

export type DashboardDistributionItem = {
  category: MoodCategory;
  count: number;
  label: string;
  share: number;
};

type EmotionStat = {
  category: MoodCategory;
  count: number;
  key: string;
  label: string;
};

const DAY_MS = 24 * 60 * 60 * 1000;
const CATEGORY_ORDER: MoodCategory[] = ["calm", "energized", "stressed", "tired"];
const CATEGORY_SCORES: Record<MoodCategory, number> = {
  calm: 1,
  energized: 2,
  stressed: -2,
  tired: -1
};

function startOfLocalDay(timestampMs: number): number {
  const date = new Date(timestampMs);
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function dayKeyFromMs(timestampMs: number): string {
  const date = new Date(timestampMs);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dayLabelFromMs(timestampMs: number): string {
  return new Date(timestampMs).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short"
  });
}

function normalizeEmotionLabel(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function buildDaySequence(timeframe: DashboardTimeframe, nowMs: number) {
  const todayStartMs = startOfLocalDay(nowMs);
  const firstDayMs = todayStartMs - (timeframe - 1) * DAY_MS;

  return Array.from({ length: timeframe }, (_, index) => {
    const dayStartMs = firstDayMs + index * DAY_MS;
    return {
      dayKey: dayKeyFromMs(dayStartMs),
      dayLabel: dayLabelFromMs(dayStartMs),
      dayStartMs
    };
  });
}

function getEmotionStats(entries: DashboardEntry[]): EmotionStat[] {
  const stats = new Map<
    string,
    {
      categoryCounts: Record<MoodCategory, number>;
      count: number;
      label: string;
    }
  >();

  for (const entry of entries) {
    const current = stats.get(entry.emotionKey) ?? {
      categoryCounts: {
        calm: 0,
        energized: 0,
        stressed: 0,
        tired: 0
      },
      count: 0,
      label: entry.emotionLabel
    };

    current.categoryCounts[entry.category] += 1;
    current.count += 1;
    current.label = entry.emotionLabel;
    stats.set(entry.emotionKey, current);
  }

  return Array.from(stats.entries())
    .map(([key, stat]) => ({
      category: CATEGORY_ORDER.reduce<MoodCategory>((leadingCategory, category) => {
        return stat.categoryCounts[category] > stat.categoryCounts[leadingCategory] ? category : leadingCategory;
      }, CATEGORY_ORDER[0]),
      count: stat.count,
      key,
      label: stat.label
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

function getDominantCategory(entries: DashboardEntry[]): MoodCategory | null {
  if (entries.length === 0) {
    return null;
  }

  const counts = {
    calm: 0,
    energized: 0,
    stressed: 0,
    tired: 0
  } satisfies Record<MoodCategory, number>;

  for (const entry of entries) {
    counts[entry.category] += 1;
  }

  return CATEGORY_ORDER.reduce<MoodCategory>((leadingCategory, category) => {
    return counts[category] > counts[leadingCategory] ? category : leadingCategory;
  }, CATEGORY_ORDER[0]);
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function getAverageCategory(entries: DashboardEntry[]): MoodCategory | null {
  if (entries.length === 0) {
    return null;
  }

  const score = average(entries.map((entry) => CATEGORY_SCORES[entry.category]));

  if (score >= 1.5) {
    return "energized";
  }
  if (score >= 0) {
    return "calm";
  }
  if (score >= -1.5) {
    return "tired";
  }

  return "stressed";
}

function getUniqueDayStarts(entries: DashboardEntry[]): number[] {
  return Array.from(new Set(entries.map((entry) => entry.dayStartMs))).sort((a, b) => b - a);
}

export function getLongestStreak(entries: DashboardEntry[]): number {
  const uniqueDaysAscending = [...new Set(entries.map((entry) => entry.dayStartMs))].sort((a, b) => a - b);

  if (uniqueDaysAscending.length === 0) {
    return 0;
  }

  let longest = 1;
  let current = 1;

  for (let index = 1; index < uniqueDaysAscending.length; index += 1) {
    if (uniqueDaysAscending[index] - uniqueDaysAscending[index - 1] === DAY_MS) {
      current += 1;
      longest = Math.max(longest, current);
      continue;
    }

    current = 1;
  }

  return longest;
}

export function getCurrentStreak(entries: DashboardEntry[], nowMs: number): number {
  const uniqueDaysDescending = getUniqueDayStarts(entries);
  if (uniqueDaysDescending.length === 0) {
    return 0;
  }

  const todayStartMs = startOfLocalDay(nowMs);
  const daysSinceLatest = Math.round((todayStartMs - uniqueDaysDescending[0]) / DAY_MS);
  if (daysSinceLatest > 1) {
    return 0;
  }

  let streak = 1;
  for (let index = 1; index < uniqueDaysDescending.length; index += 1) {
    if (uniqueDaysDescending[index - 1] - uniqueDaysDescending[index] === DAY_MS) {
      streak += 1;
      continue;
    }

    break;
  }

  return streak;
}

function formatRelativeTime(createdAtSeconds: number, nowMs: number): string {
  const targetMs = createdAtSeconds * 1000;
  const diffMs = targetMs - nowMs;
  const absoluteDiffMs = Math.abs(diffMs);
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;

  if (absoluteDiffMs < minuteMs) {
    return diffMs >= 0 ? "in <1m" : "just now";
  }

  if (absoluteDiffMs < hourMs) {
    const minutes = Math.max(1, Math.floor(absoluteDiffMs / minuteMs));
    return diffMs >= 0 ? `in ${minutes}m` : `${minutes}m ago`;
  }

  if (absoluteDiffMs < DAY_MS) {
    const hours = Math.max(1, Math.floor(absoluteDiffMs / hourMs));
    return diffMs >= 0 ? `in ${hours}h` : `${hours}h ago`;
  }

  const days = Math.max(1, Math.floor(absoluteDiffMs / DAY_MS));
  if (days < 7) {
    return diffMs >= 0 ? `in ${days}d` : `${days}d ago`;
  }

  return new Date(targetMs).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short"
  });
}

function buildRecentTrendInsight(entries: DashboardEntry[]): string | null {
  const buckets = new Map<number, number[]>();

  for (const entry of entries) {
    const current = buckets.get(entry.dayStartMs) ?? [];
    current.push(CATEGORY_SCORES[entry.category]);
    buckets.set(entry.dayStartMs, current);
  }

  const activeDayScores = Array.from(buckets.entries())
    .sort(([dayA], [dayB]) => dayA - dayB)
    .map(([, scores]) => average(scores));

  if (activeDayScores.length < 4) {
    return null;
  }

  const recentScores = activeDayScores.slice(-3);
  const previousScores = activeDayScores.slice(-6, -3);
  if (previousScores.length === 0) {
    return null;
  }

  const delta = average(recentScores) - average(previousScores);
  if (delta >= 0.75) {
    return "The last few check-ins are leaning calmer than the start of the week.";
  }
  if (delta <= -0.75) {
    return "Stress and fatigue have picked up over the last few check-ins.";
  }

  return null;
}

function buildWeekdayInsight(entries: DashboardEntry[]): string | null {
  const weekdayEntries = entries.filter((entry) => !entry.isWeekend);
  if (weekdayEntries.length < 3) {
    return null;
  }

  const weekendEntries = entries.filter((entry) => entry.isWeekend);
  const weekdayCategory = getDominantCategory(weekdayEntries);
  const weekendCategory = getDominantCategory(weekendEntries);

  if (!weekdayCategory) {
    return null;
  }

  if (weekendEntries.length >= 2 && weekendCategory && weekendCategory !== weekdayCategory) {
    return `Weekdays lean ${formatMoodCategory(weekdayCategory).toLowerCase()} while weekends lean ${formatMoodCategory(weekendCategory).toLowerCase()}.`;
  }

  return `${formatMoodCategory(weekdayCategory)} shows up most on weekdays.`;
}

export function getDashboardEntries(features: FeatureRecord[]): DashboardEntry[] {
  return features
    .map((feature) => {
      const categoryValue =
        typeof feature.label?.category === "string" ? feature.label.category.trim().toLowerCase() : null;
      const emotionValue = typeof feature.label?.emotion === "string" ? normalizeEmotionLabel(feature.label.emotion) : "";

      if (!categoryValue || !isMoodCategory(categoryValue) || !emotionValue) {
        return null;
      }

      const createdAtMs = feature.createdAt * 1000;
      const dayStartMs = startOfLocalDay(createdAtMs);

      return {
        category: categoryValue,
        createdAt: feature.createdAt,
        dayKey: dayKeyFromMs(createdAtMs),
        dayLabel: dayLabelFromMs(createdAtMs),
        dayStartMs,
        emotionKey: emotionValue.toLowerCase(),
        emotionLabel: emotionValue,
        id: feature.id,
        isWeekend: [0, 6].includes(new Date(createdAtMs).getDay())
      };
    })
    .filter((entry): entry is DashboardEntry => entry !== null)
    .sort((a, b) => b.createdAt - a.createdAt);
}

export function filterEntriesByTimeframe(
  entries: DashboardEntry[],
  timeframe: DashboardTimeframe,
  nowMs: number
): DashboardEntry[] {
  const firstDayMs = startOfLocalDay(nowMs) - (timeframe - 1) * DAY_MS;
  const endExclusiveMs = startOfLocalDay(nowMs) + DAY_MS;

  return entries.filter((entry) => entry.dayStartMs >= firstDayMs && entry.dayStartMs < endExclusiveMs);
}

export function buildDashboardSummary(entries: DashboardEntry[], nowMs: number): DashboardSummary {
  const todayDayKey = dayKeyFromMs(nowMs);
  const todayEntries = entries.filter((entry) => entry.dayKey === todayDayKey);
  const primaryEntry = todayEntries[0] ?? entries[0] ?? null;

  if (!primaryEntry) {
    return {
      entriesToday: 0,
      isToday: false,
      lastLogged: "No entries yet",
      message: "Log your first mood to unlock a daily snapshot.",
      primaryEntry: null
    };
  }

  return {
    entriesToday: todayEntries.length,
    isToday: todayEntries.length > 0,
    lastLogged: formatRelativeTime(primaryEntry.createdAt, nowMs),
    message:
      todayEntries.length > 0
        ? "Latest check-in from today."
        : "No entry logged today. Showing your latest mood.",
    primaryEntry
  };
}

export function buildDashboardMetrics(entries: DashboardEntry[], nowMs: number): DashboardMetric[] {
  const weekEntries = filterEntriesByTimeframe(entries, 7, nowMs);
  const topEmotion = getEmotionStats(weekEntries)[0] ?? null;
  const averageCategory = getAverageCategory(weekEntries);
  const longestStreak = getLongestStreak(entries);

  return [
    {
      detail: "last 7 days",
      icon: "7D",
      key: "entries-week",
      label: "Entries this week",
      tone: "primary",
      value: String(weekEntries.length)
    },
    {
      detail: topEmotion ? formatMoodCategory(topEmotion.category) : "need labels",
      icon: "TOP",
      key: "top-emotion",
      label: "Most common mood",
      tone: topEmotion?.category ?? "neutral",
      value: topEmotion?.label ?? "No data"
    },
    {
      detail: "rolling 7 days",
      icon: "AVG",
      key: "average-category",
      label: "Average category",
      tone: averageCategory ?? "neutral",
      value: averageCategory ? formatMoodCategory(averageCategory) : "No data"
    },
    {
      detail: longestStreak > 0 ? "best run" : "start logging",
      icon: "RUN",
      key: "longest-streak",
      label: "Longest streak",
      tone: longestStreak > 0 ? "primary" : "neutral",
      value: longestStreak > 0 ? `${longestStreak} day${longestStreak === 1 ? "" : "s"}` : "0 days"
    }
  ];
}

export function buildMoodTrendChart(
  entries: DashboardEntry[],
  mode: DashboardChartMode,
  timeframe: DashboardTimeframe,
  nowMs: number
): {
  points: DashboardChartPoint[];
  series: DashboardChartSeries[];
} {
  const days = buildDaySequence(timeframe, nowMs);
  const buckets = new Map<
    string,
    {
      categoryCounts: Record<MoodCategory, number>;
      emotionCounts: Map<string, number>;
      label: string;
    }
  >();

  for (const day of days) {
    buckets.set(day.dayKey, {
      categoryCounts: {
        calm: 0,
        energized: 0,
        stressed: 0,
        tired: 0
      },
      emotionCounts: new Map<string, number>(),
      label: day.dayLabel
    });
  }

  for (const entry of entries) {
    const bucket = buckets.get(entry.dayKey);
    if (!bucket) {
      continue;
    }

    bucket.categoryCounts[entry.category] += 1;
    bucket.emotionCounts.set(entry.emotionKey, (bucket.emotionCounts.get(entry.emotionKey) ?? 0) + 1);
  }

  if (mode === "category") {
    const series: DashboardChartSeries[] = CATEGORY_ORDER.map((category) => ({
      category,
      key: category,
      label: formatMoodCategory(category)
    }));

    const points = days.map((day) => {
      const bucket = buckets.get(day.dayKey);
      const values = CATEGORY_ORDER.reduce<Record<string, number>>((currentValues, category) => {
        currentValues[category] = bucket?.categoryCounts[category] ?? 0;
        return currentValues;
      }, {});

      return {
        key: day.dayKey,
        label: day.dayLabel,
        total: CATEGORY_ORDER.reduce((sum, category) => sum + (bucket?.categoryCounts[category] ?? 0), 0),
        values
      };
    });

    return { points, series };
  }

  const emotionStats = getEmotionStats(entries).slice(0, 6);
  const series: DashboardChartSeries[] = emotionStats.map((stat) => ({
    category: stat.category,
    key: stat.key,
    label: stat.label
  }));

  const points = days.map((day) => {
    const bucket = buckets.get(day.dayKey);
    const values = emotionStats.reduce<Record<string, number>>((currentValues, stat) => {
      currentValues[stat.key] = bucket?.emotionCounts.get(stat.key) ?? 0;
      return currentValues;
    }, {});

    return {
      key: day.dayKey,
      label: day.dayLabel,
      total: emotionStats.reduce((sum, stat) => sum + (bucket?.emotionCounts.get(stat.key) ?? 0), 0),
      values
    };
  });

  return { points, series };
}

export function buildCategoryDistribution(entries: DashboardEntry[]): DashboardDistributionItem[] {
  const totalEntries = entries.length;
  const counts = {
    calm: 0,
    energized: 0,
    stressed: 0,
    tired: 0
  } satisfies Record<MoodCategory, number>;

  for (const entry of entries) {
    counts[entry.category] += 1;
  }

  return CATEGORY_ORDER.map((category) => ({
    category,
    count: counts[category],
    label: formatMoodCategory(category),
    share: totalEntries > 0 ? counts[category] / totalEntries : 0
  }));
}

export function buildDashboardInsights(entries: DashboardEntry[], nowMs: number): string[] {
  const insights: string[] = [];
  const weekEntries = filterEntriesByTimeframe(entries, 7, nowMs);
  const monthEntries = filterEntriesByTimeframe(entries, 30, nowMs);
  const topEmotion = getEmotionStats(weekEntries)[0] ?? null;
  const trendInsight = buildRecentTrendInsight(weekEntries);
  const weekdayInsight = buildWeekdayInsight(monthEntries);
  const currentStreak = getCurrentStreak(entries, nowMs);
  const longestStreak = getLongestStreak(entries);

  if (topEmotion) {
    insights.push(`Your most common mood this week is ${topEmotion.label}.`);
  }

  if (trendInsight) {
    insights.push(trendInsight);
  }

  if (currentStreak >= 2) {
    insights.push(`You logged moods ${currentStreak} days in a row.`);
  } else if (longestStreak >= 3) {
    insights.push(`Your best logging streak so far is ${longestStreak} days.`);
  }

  if (weekdayInsight) {
    insights.push(weekdayInsight);
  }

  if (insights.length === 0) {
    insights.push("Log moods across a few days to start surfacing patterns here.");
  }

  return insights.slice(0, 3);
}
