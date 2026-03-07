import type { FeatureData, FeatureRecord } from "../types/features";

export type FeatureSectionTitle =
  | "Activity"
  | "Heart / Recovery"
  | "Sleep"
  | "Daily / Context"
  | "Personal / Baseline"
  | "Other";

export type FeatureSectionRow = {
  id: string;
  label: string;
  value: string;
};

export type FeatureSection = {
  title: FeatureSectionTitle;
  rows: FeatureSectionRow[];
};

export type FeatureMetadataViewModel = {
  source: string;
  createdAt: string;
  extractorVersion: string;
  windowStart: string;
  windowEnd: string;
  sourceTimezone: string;
};

export type FeatureKeyMetric = {
  key: string;
  label: string;
  value: string;
};

const SECTION_ORDER: FeatureSectionTitle[] = [
  "Activity",
  "Heart / Recovery",
  "Sleep",
  "Daily / Context",
  "Personal / Baseline",
  "Other"
];

const CLASSIFICATION_PRIORITY: FeatureSectionTitle[] = [
  "Personal / Baseline",
  "Sleep",
  "Heart / Recovery",
  "Activity",
  "Daily / Context"
];

const SECTION_KEYWORDS: Record<FeatureSectionTitle, string[]> = {
  Activity: [
    "step",
    "activity",
    "active",
    "exercise",
    "workout",
    "distance",
    "calorie",
    "azm",
    "sedentary"
  ],
  "Heart / Recovery": [
    "heart",
    "resting",
    "hr",
    "bpm",
    "hrv",
    "rmssd",
    "recovery",
    "rhr"
  ],
  Sleep: [
    "sleep",
    "bed",
    "wake",
    "rem",
    "deep",
    "waso",
    "fragmentation",
    "night"
  ],
  "Daily / Context": [
    "day",
    "hour",
    "weekday",
    "weekend",
    "time",
    "context",
    "location",
    "weather",
    "aqi",
    "timezone",
    "local"
  ],
  "Personal / Baseline": [
    "baseline",
    "personal",
    "avg",
    "mean",
    "norm",
    "deviation",
    "trend",
    "std",
    "rolling"
  ],
  Other: []
};

const SECTION_DESCRIPTIONS: Record<FeatureSectionTitle, string> = {
  Activity: "Movement, activity, and exertion signals from this snapshot.",
  "Heart / Recovery": "Heart-rate and recovery markers captured around this moment.",
  Sleep: "Sleep-related signals that help explain the snapshot context.",
  "Daily / Context": "Time, day, and contextual signals linked to this capture.",
  "Personal / Baseline": "Baseline or comparison metrics used to interpret the snapshot.",
  Other: "Additional values that do not fit neatly into the main groups."
};

const NON_SECTION_KEYS = new Set(["meta", "notes", "clientFeatures", "client_features"]);

const LABEL_OVERRIDES: Record<string, string> = {
  resting_hr: "Resting Heart Rate",
  sleep_efficiency: "Sleep Efficiency",
  sleep_efficiency_pct: "Sleep Efficiency",
  weekday_flag: "Weekday Indicator",
  day_of_week: "Day Of Week",
  hour_of_day: "Hour Of Day",
  is_weekend: "Weekend Indicator",
  source_timezone: "Source Timezone",
  window_start: "Window Start",
  window_end: "Window End",
  extractor_version: "Extractor Version",
  steps_count: "Steps",
  active_zone_minutes: "Active Minutes",
  avg_bpm: "Average Heart Rate",
  calories_out_kcal: "Calories Burned",
  burned_kcal: "Calories Burned",
  total_sleep_minutes: "Sleep Duration",
  daily_rmssd: "HRV (RMSSD)"
};

const WEEKDAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday"
];

type FlatFeatureValue = {
  path: string;
  value: unknown;
};

type KeyMetricDefinition = {
  key: string;
  label: string;
  paths: string[];
  formatter?: (value: unknown) => string | null;
};

const KEY_METRIC_DEFINITIONS: KeyMetricDefinition[] = [
  {
    key: "sleep-duration",
    label: "Sleep",
    paths: ["sleep.total_sleep_minutes", "sleep.minutes_asleep", "sleep.totalSleepMinutes"],
    formatter: (value) => formatMinutesAsDuration(toFiniteNumber(value))
  },
  {
    key: "steps",
    label: "Steps",
    paths: ["activity.steps_count", "activity.step_count", "activity.steps", "activity.stepsCount"],
    formatter: (value) => formatCountValue(toFiniteNumber(value))
  },
  {
    key: "active-minutes",
    label: "Active Minutes",
    paths: [
      "activity.active_zone_minutes",
      "activity.active_minutes",
      "activity.activeZoneMinutes",
      "activity.activeMinutes"
    ],
    formatter: (value) => formatMinutesValue(toFiniteNumber(value))
  },
  {
    key: "resting-hr",
    label: "Resting HR",
    paths: [
      "heart_rate.resting_hr",
      "resting_hr.resting_hr",
      "resting_hr_features.resting_hr",
      "derived.resting_hr"
    ],
    formatter: (value) => formatBpmValue(toFiniteNumber(value))
  },
  {
    key: "average-hr",
    label: "Average HR",
    paths: ["heart_rate.avg_bpm", "heart_rate.average_bpm", "heart_rate.avgBpm"],
    formatter: (value) => formatBpmValue(toFiniteNumber(value))
  },
  {
    key: "calories-burned",
    label: "Calories Burned",
    paths: [
      "activity.calories_out_kcal",
      "activity.calories_burned_kcal",
      "calories.burned_kcal",
      "calories.calories_burned_kcal",
      "derived.caloriesOutToday"
    ],
    formatter: (value) => formatCaloriesValue(toFiniteNumber(value))
  },
  {
    key: "sleep-efficiency",
    label: "Sleep Efficiency",
    paths: ["sleep.sleep_efficiency_pct", "sleep.sleep_efficiency", "sleep.sleepEfficiencyPct"],
    formatter: (value) => formatPercentValue(toFiniteNumber(value))
  },
  {
    key: "hrv",
    label: "HRV",
    paths: ["hrv.daily_rmssd", "derived.hrvRmssdDaily"],
    formatter: (value) => formatMillisecondValue(toFiniteNumber(value))
  }
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function pickString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function toSnakeCase(value: string): string {
  return value
    .replace(/([a-z])([A-Z])/g, "$1_$2")
    .replace(/[-\s]+/g, "_")
    .toLowerCase();
}

function normalizePath(path: string): string {
  return path
    .split(".")
    .filter(Boolean)
    .map((segment) => toSnakeCase(segment))
    .join(".");
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return value.toLocaleString();
  }

  const rounded = Number(value.toFixed(2));
  return rounded.toLocaleString(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: rounded % 1 === 0 ? 0 : 1
  });
}

function formatCountValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return formatNumber(value);
}

function formatMinutesAsDuration(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  const totalMinutes = Math.max(0, Math.round(value));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) {
    return `${minutes} min`;
  }

  return `${hours}h ${String(minutes).padStart(2, "0")}m`;
}

function formatMinutesValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `${formatNumber(value)} min`;
}

function formatBpmValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `${formatNumber(value)} bpm`;
}

function formatCaloriesValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `${formatNumber(value)} kcal`;
}

function formatMillisecondValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `${formatNumber(value)} ms`;
}

function formatPercentValue(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `${formatNumber(value)}%`;
}

function formatRatioAsPercent(value: number): string {
  if (value <= 1) {
    return `${formatNumber(value * 100)}%`;
  }

  return `${formatNumber(value)}%`;
}

function isLikelyTimestampKey(path: string): boolean {
  const normalized = normalizePath(path);
  return (
    normalized.includes("time") ||
    normalized.endsWith("at") ||
    normalized.endsWith("_at") ||
    normalized.includes("date")
  );
}

function isDayOfWeekPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.endsWith("day_of_week");
}

function isHourOfDayPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.endsWith("hour_of_day");
}

function isSleepDurationPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.includes("sleep.total_sleep_minutes") || normalized.endsWith("minutes_asleep");
}

function isMinutesPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.includes("minute");
}

function isPercentPath(path: string): boolean {
  const normalized = normalizePath(path);
  return (
    normalized.includes("pct") ||
    normalized.includes("percent") ||
    normalized.includes("percentage") ||
    normalized.includes("efficiency") ||
    normalized.endsWith("coverage") ||
    normalized.includes("fraction")
  );
}

function isFractionPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.endsWith("coverage") || normalized.includes("fraction");
}

function isBpmPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.includes("bpm") || normalized.endsWith("resting_hr");
}

function isCaloriesPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.includes("calorie") || normalized.includes("kcal");
}

function isRmssdPath(path: string): boolean {
  const normalized = normalizePath(path);
  return normalized.includes("rmssd");
}

function formatHourOfDay(value: number): string {
  const hour = Math.max(0, Math.min(23, Math.round(value)));
  const suffix = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:00 ${suffix}`;
}

function formatDayOfWeek(value: number): string | null {
  const index = Math.round(value) - 1;
  if (index < 0 || index >= WEEKDAY_LABELS.length) {
    return null;
  }

  return WEEKDAY_LABELS[index];
}

function formatTimestampValue(value: number | string): string | null {
  const parsed = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toLocaleString(undefined, {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function toFiniteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function getValueAtPath(data: FeatureData, path: string): unknown {
  let current: unknown = data;
  for (const key of path.split(".")) {
    if (!isRecord(current) || !(key in current)) {
      return undefined;
    }
    current = current[key];
  }
  return current;
}

function flattenFeatureData(data: FeatureData, prefix = ""): FlatFeatureValue[] {
  const flattened: FlatFeatureValue[] = [];

  for (const [key, value] of Object.entries(data)) {
    if (NON_SECTION_KEYS.has(key)) {
      continue;
    }

    const path = prefix ? `${prefix}.${key}` : key;
    if (isRecord(value)) {
      flattened.push(...flattenFeatureData(value, path));
      continue;
    }

    flattened.push({ path, value });
  }

  return flattened;
}

function classifySection(path: string): FeatureSectionTitle {
  const normalizedPath = normalizePath(path);

  for (const section of CLASSIFICATION_PRIORITY) {
    if (SECTION_KEYWORDS[section].some((keyword) => normalizedPath.includes(keyword))) {
      return section;
    }
  }

  return "Other";
}

export function formatFeatureSourceLabel(source: string): string {
  if (source === "fitbit-pipeline") {
    return "Fitbit";
  }

  return source
    .split(/[-_]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function formatFeatureLabel(path: string): string {
  const key = path.split(".").pop() ?? path;
  const snakeKey = toSnakeCase(key);
  if (LABEL_OVERRIDES[snakeKey]) {
    return LABEL_OVERRIDES[snakeKey];
  }

  const spaced = key.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/[_-]+/g, " ");
  return spaced.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatFeatureValue(value: unknown, path = ""): string {
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    if (isLikelyTimestampKey(path) && value > 1_000_000_000) {
      const formattedTimestamp = formatTimestampValue(value);
      if (formattedTimestamp) {
        return formattedTimestamp;
      }
    }

    if (isDayOfWeekPath(path)) {
      const weekday = formatDayOfWeek(value);
      if (weekday) {
        return weekday;
      }
    }

    if (isHourOfDayPath(path)) {
      return formatHourOfDay(value);
    }

    if (isSleepDurationPath(path)) {
      return formatMinutesAsDuration(value) ?? "N/A";
    }

    if (isPercentPath(path)) {
      return isFractionPath(path) ? formatRatioAsPercent(value) : formatPercentValue(value) ?? "N/A";
    }

    if (isBpmPath(path)) {
      return formatBpmValue(value) ?? "N/A";
    }

    if (isCaloriesPath(path)) {
      return formatCaloriesValue(value) ?? "N/A";
    }

    if (isRmssdPath(path)) {
      return formatMillisecondValue(value) ?? "N/A";
    }

    if (isMinutesPath(path)) {
      return formatMinutesValue(value) ?? "N/A";
    }

    return formatNumber(value);
  }

  if (typeof value === "string") {
    if (isLikelyTimestampKey(path)) {
      const formattedTimestamp = formatTimestampValue(value);
      if (formattedTimestamp) {
        return formattedTimestamp;
      }
    }
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => formatFeatureValue(item, path)).join(", ");
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function buildFeatureSections(data: FeatureData): FeatureSection[] {
  const rowsBySection: Record<FeatureSectionTitle, FeatureSectionRow[]> = {
    Activity: [],
    "Heart / Recovery": [],
    Sleep: [],
    "Daily / Context": [],
    "Personal / Baseline": [],
    Other: []
  };

  for (const item of flattenFeatureData(data)) {
    const section = classifySection(item.path);
    rowsBySection[section].push({
      id: item.path,
      label: formatFeatureLabel(item.path),
      value: formatFeatureValue(item.value, item.path)
    });
  }

  return SECTION_ORDER.map((title) => ({
    title,
    rows: rowsBySection[title]
  })).filter((section) => section.rows.length > 0);
}

export function getFeatureSectionDescription(title: FeatureSectionTitle): string {
  return SECTION_DESCRIPTIONS[title];
}

export function extractFeatureKeyMetrics(data: FeatureData): FeatureKeyMetric[] {
  const metrics: FeatureKeyMetric[] = [];

  for (const definition of KEY_METRIC_DEFINITIONS) {
    let matchedValue: string | null = null;

    for (const path of definition.paths) {
      const candidate = getValueAtPath(data, path);
      if (candidate === null || candidate === undefined) {
        continue;
      }

      const formatted = definition.formatter ? definition.formatter(candidate) : formatFeatureValue(candidate, path);
      if (!formatted || formatted === "N/A") {
        continue;
      }

      matchedValue = formatted;
      break;
    }

    if (!matchedValue) {
      continue;
    }

    metrics.push({
      key: definition.key,
      label: definition.label,
      value: matchedValue
    });
  }

  return metrics.slice(0, 6);
}

export function formatTimestamp(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "N/A";
  }

  const formatted = formatTimestampValue(value);
  if (formatted) {
    return formatted;
  }

  return String(value);
}

export function buildFeatureSnapshotContextLine(source: string): string {
  const sourceLabel = formatFeatureSourceLabel(source);
  if (sourceLabel === "Fitbit") {
    return "Captured after a recent Fitbit sync.";
  }

  return `Captured from ${sourceLabel}.`;
}

export function extractFeatureMetadata(feature: FeatureRecord): FeatureMetadataViewModel {
  const meta = isRecord(feature.data.meta) ? feature.data.meta : {};

  const extractorVersion =
    pickString(feature.extractorVersion) ??
    pickString(meta.extractorVersion) ??
    pickString(meta.extractor_version) ??
    "N/A";
  const windowStart =
    pickString(feature.windowStart) ??
    pickString(meta.windowStart) ??
    pickString(meta.window_start) ??
    "N/A";
  const windowEnd =
    pickString(feature.windowEnd) ?? pickString(meta.windowEnd) ?? pickString(meta.window_end) ?? "N/A";
  const sourceTimezone =
    pickString(feature.sourceTimezone) ??
    pickString(meta.sourceTimezone) ??
    pickString(meta.source_timezone) ??
    "N/A";

  return {
    source: formatFeatureSourceLabel(feature.source),
    createdAt: formatTimestamp(feature.createdAt),
    extractorVersion,
    windowStart: formatTimestamp(windowStart),
    windowEnd: formatTimestamp(windowEnd),
    sourceTimezone
  };
}
