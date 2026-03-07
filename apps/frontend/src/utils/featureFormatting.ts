import type { FeatureData, FeatureRecord } from "../types/features";

export type FeatureSectionTitle =
  | "Activity"
  | "Heart / Recovery"
  | "Sleep"
  | "Daily / Context"
  | "Personal / Baseline"
  | "Other";

export type FeatureSectionRow = {
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

const NON_SECTION_KEYS = new Set(["meta", "notes", "clientFeatures", "client_features"]);

const LABEL_OVERRIDES: Record<string, string> = {
  resting_hr: "Resting Heart Rate",
  sleep_efficiency: "Sleep Efficiency",
  weekday_flag: "Weekday Indicator",
  day_of_week: "Day Of Week",
  is_weekend: "Weekend Indicator",
  source_timezone: "Source Timezone",
  window_start: "Window Start",
  window_end: "Window End",
  extractor_version: "Extractor Version"
};

type FlatFeatureValue = {
  path: string;
  value: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function pickString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }

  const rounded = value.toFixed(2);
  return rounded.replace(/\.?0+$/, "");
}

function isLikelyTimestampKey(path: string): boolean {
  const normalized = path.toLowerCase();
  return (
    normalized.includes("time") ||
    normalized.endsWith("at") ||
    normalized.endsWith("_at") ||
    normalized.includes("date")
  );
}

function formatTimestampValue(value: number | string): string | null {
  const parsed = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toLocaleString();
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

function toSnakeCase(value: string): string {
  return value
    .replace(/([a-z])([A-Z])/g, "$1_$2")
    .replace(/[-\s]+/g, "_")
    .toLowerCase();
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
  const normalizedPath = path.toLowerCase();

  for (const section of CLASSIFICATION_PRIORITY) {
    if (SECTION_KEYWORDS[section].some((keyword) => normalizedPath.includes(keyword))) {
      return section;
    }
  }

  return "Other";
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
      label: formatFeatureLabel(item.path),
      value: formatFeatureValue(item.value, item.path)
    });
  }

  return SECTION_ORDER.map((title) => ({
    title,
    rows: rowsBySection[title]
  })).filter((section) => section.rows.length > 0);
}

export function formatTimestamp(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "N/A";
  }

  const parsed = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return parsed.toLocaleString();
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
    source: feature.source,
    createdAt: formatTimestamp(feature.createdAt),
    extractorVersion,
    windowStart: formatTimestamp(windowStart),
    windowEnd: formatTimestamp(windowEnd),
    sourceTimezone
  };
}
