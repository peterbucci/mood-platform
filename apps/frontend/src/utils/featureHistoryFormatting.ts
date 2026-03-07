import type { FeatureData, FeatureRecord } from "../types/features";
import type { MoodCategory } from "../types/mood";
import { formatMoodCategory, getMoodDisplayModel } from "./moodFormatting";

export type FeatureHistoryGroup = {
  key: string;
  title: string;
  features: FeatureRecord[];
};

export type FeatureCategorySummary = {
  category: MoodCategory | null;
  label: string;
  detail: string;
};

const NON_GROUP_DATA_KEYS = new Set(["meta", "notes", "clientFeatures", "client_features"]);

function pluralize(value: number, singular: string): string {
  return value === 1 ? singular : `${singular}s`;
}

function toMoodCategory(value: string | null | undefined): MoodCategory | null {
  if (value === "energized" || value === "calm" || value === "stressed" || value === "tired") {
    return value;
  }

  return null;
}

function toFeatureDate(createdAt: number): Date | null {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed;
}

function isSameLocalDay(left: Date, right: Date): boolean {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  );
}

function isYesterday(date: Date, now: Date): boolean {
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  return isSameLocalDay(date, yesterday);
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit"
  });
}

function formatDayKey(date: Date): string {
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()].join("-");
}

export function sortFeaturesByNewest(features: FeatureRecord[]): FeatureRecord[] {
  return [...features].sort((left, right) => right.createdAt - left.createdAt);
}

export function shortenFeatureId(featureId: string): string {
  if (featureId.length <= 18) {
    return featureId;
  }

  return `${featureId.slice(0, 4)}...${featureId.slice(-4)}`;
}

export function formatFeatureSource(source: string): string {
  if (source === "fitbit-pipeline") {
    return "Fitbit";
  }

  return source
    .split(/[-_]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function formatFeatureTimestamp(createdAt: number): string {
  const parsed = toFeatureDate(createdAt);
  if (!parsed) {
    return String(createdAt);
  }

  return parsed.toLocaleString(undefined, {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short"
  });
}

export function formatFeatureRelativeTime(createdAt: number, nowMs: number = Date.now()): string {
  const targetMs = createdAt * 1000;
  const diffMs = nowMs - targetMs;
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (diffMs < minuteMs) {
    return "Just now";
  }

  if (diffMs < hourMs) {
    const minutes = Math.max(1, Math.floor(diffMs / minuteMs));
    return `${minutes}m ago`;
  }

  if (diffMs < dayMs) {
    const hours = Math.max(1, Math.floor(diffMs / hourMs));
    return `${hours}h ago`;
  }

  if (diffMs < dayMs * 7) {
    const days = Math.max(1, Math.floor(diffMs / dayMs));
    return `${days}d ago`;
  }

  return formatFeatureTimestamp(createdAt);
}

export function formatFeatureCaptureTime(createdAt: number, nowMs: number = Date.now()): string {
  const parsed = toFeatureDate(createdAt);
  if (!parsed) {
    return `Captured ${createdAt}`;
  }

  const now = new Date(nowMs);
  const time = formatTime(parsed);
  if (isSameLocalDay(parsed, now)) {
    return `Captured today at ${time}`;
  }
  if (isYesterday(parsed, now)) {
    return `Captured yesterday at ${time}`;
  }

  const dayLabel = parsed.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short"
  });
  return `Captured ${dayLabel} at ${time}`;
}

export function countFeatureDataGroups(data: FeatureData): number {
  return Object.keys(data).filter((key) => !NON_GROUP_DATA_KEYS.has(key)).length;
}

export function getMostCommonRecentCategory(
  features: FeatureRecord[],
  sampleSize = 7
): FeatureCategorySummary {
  const recentFeatures = sortFeaturesByNewest(features).slice(0, sampleSize);
  const categoryCounts = new Map<MoodCategory, { count: number; firstSeenIndex: number }>();

  recentFeatures.forEach((feature, index) => {
    const mood = getMoodDisplayModel(feature.label);
    const category = toMoodCategory(feature.label?.category?.toLowerCase());

    if (mood.state !== "labeled" || !category) {
      return;
    }

    const current = categoryCounts.get(category);
    if (current) {
      current.count += 1;
      return;
    }

    categoryCounts.set(category, { count: 1, firstSeenIndex: index });
  });

  if (!recentFeatures.length) {
    return {
      category: null,
      label: "No captures",
      detail: "Capture history will appear here."
    };
  }

  if (!categoryCounts.size) {
    return {
      category: null,
      label: "No labels",
      detail: "Add mood labels to surface recent patterns."
    };
  }

  const [category, stats] = [...categoryCounts.entries()].sort(
    (left, right) =>
      right[1].count - left[1].count || left[1].firstSeenIndex - right[1].firstSeenIndex
  )[0];

  return {
    category,
    label: formatMoodCategory(category),
    detail: `${stats.count} of last ${recentFeatures.length} ${pluralize(recentFeatures.length, "capture")}`
  };
}

export function groupFeaturesByDate(
  features: FeatureRecord[],
  nowMs: number = Date.now()
): FeatureHistoryGroup[] {
  const now = new Date(nowMs);
  const groupsByKey = new Map<string, FeatureHistoryGroup>();

  sortFeaturesByNewest(features).forEach((feature) => {
    const parsed = toFeatureDate(feature.createdAt);
    const key = parsed ? formatDayKey(parsed) : "unknown";
    let title = "Unknown date";

    if (parsed) {
      if (isSameLocalDay(parsed, now)) {
        title = "Today";
      } else if (isYesterday(parsed, now)) {
        title = "Yesterday";
      } else {
        title = parsed.toLocaleDateString(undefined, {
          day: "numeric",
          month: "long",
          weekday: "long"
        });
      }
    }

    const existing = groupsByKey.get(key);
    if (existing) {
      existing.features.push(feature);
      return;
    }

    groupsByKey.set(key, {
      key,
      title,
      features: [feature]
    });
  });

  return [...groupsByKey.values()];
}
