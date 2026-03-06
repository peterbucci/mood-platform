import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getLatestFeature } from "../api/features";
import FeatureMetadataCard from "../components/dashboard/FeatureMetadataCard";
import FeatureSectionCard from "../components/dashboard/FeatureSectionCard";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureData, FeatureRecord } from "../types/features";

type DashboardViewState = "loading" | "ready" | "empty" | "error";

type FlatFeatureValue = {
  path: string;
  value: unknown;
};

type FeatureSection = {
  title: "Activity" | "Heart / Recovery" | "Sleep" | "Daily / Context" | "Personal / Baseline";
  rows: Array<{ label: string; value: string }>;
};

const SECTION_ORDER: FeatureSection["title"][] = [
  "Activity",
  "Heart / Recovery",
  "Sleep",
  "Daily / Context",
  "Personal / Baseline"
];

const NON_SECTION_KEYS = new Set(["meta", "notes", "clientFeatures", "client_features"]);

const SECTION_KEYWORDS: Record<FeatureSection["title"], string[]> = {
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
    "hr",
    "bpm",
    "hrv",
    "rmssd",
    "resting",
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
    "debt",
    "night"
  ],
  "Daily / Context": [
    "day",
    "hour",
    "weekend",
    "weekday",
    "time",
    "context",
    "weather",
    "location",
    "aqi",
    "timezone",
    "local"
  ],
  "Personal / Baseline": [
    "baseline",
    "avg",
    "mean",
    "trend",
    "deviation",
    "std",
    "z",
    "personal",
    "rolling"
  ]
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function humanizeKey(path: string): string {
  const segment = path.split(".").pop() ?? path;
  const spaced = segment.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/[_-]+/g, " ");
  return spaced.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }
  const rounded = value.toFixed(2);
  return rounded.replace(/\.?0+$/, "");
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "N/A";
  }
  if (typeof value === "number") {
    return formatNumber(value);
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => formatValue(item)).join(", ");
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
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

function classifySection(path: string): FeatureSection["title"] {
  const normalizedPath = path.toLowerCase();

  for (const section of SECTION_ORDER) {
    if (SECTION_KEYWORDS[section].some((keyword) => normalizedPath.includes(keyword))) {
      return section;
    }
  }

  return "Daily / Context";
}

function buildSections(data: FeatureData): FeatureSection[] {
  const rowsBySection: Record<FeatureSection["title"], Array<{ label: string; value: string }>> = {
    Activity: [],
    "Heart / Recovery": [],
    Sleep: [],
    "Daily / Context": [],
    "Personal / Baseline": []
  };

  for (const item of flattenFeatureData(data)) {
    const section = classifySection(item.path);
    rowsBySection[section].push({
      label: humanizeKey(item.path),
      value: formatValue(item.value)
    });
  }

  return SECTION_ORDER.map((title) => ({
    title,
    rows: rowsBySection[title]
  }));
}

function formatTimestamp(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "N/A";
  }

  const parsed =
    typeof value === "number" ? new Date(value * 1000) : new Date(typeof value === "string" ? value : "");
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }

  return parsed.toLocaleString();
}

function readString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function extractMetadata(feature: FeatureRecord) {
  const meta = isRecord(feature.data.meta) ? feature.data.meta : {};

  const extractorVersion =
    readString(feature.extractorVersion) ??
    readString(meta.extractorVersion) ??
    readString(meta.extractor_version) ??
    "N/A";

  const windowStart =
    readString(feature.windowStart) ??
    readString(meta.windowStart) ??
    readString(meta.window_start) ??
    "N/A";

  const windowEnd =
    readString(feature.windowEnd) ?? readString(meta.windowEnd) ?? readString(meta.window_end) ?? "N/A";

  const sourceTimezone =
    readString(feature.sourceTimezone) ??
    readString(meta.sourceTimezone) ??
    readString(meta.source_timezone) ??
    "N/A";

  return {
    createdAt: formatTimestamp(feature.createdAt),
    source: feature.source,
    extractorVersion,
    windowStart: formatTimestamp(windowStart),
    windowEnd: formatTimestamp(windowEnd),
    sourceTimezone
  };
}

export default function DashboardPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [viewState, setViewState] = useState<DashboardViewState>("loading");
  const [latestFeature, setLatestFeature] = useState<FeatureRecord | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadLatestFeature = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);

    try {
      const feature = await getLatestFeature();
      if (feature === null) {
        setLatestFeature(null);
        setViewState("empty");
        return;
      }
      setLatestFeature(feature);
      setViewState("ready");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load dashboard data.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, []);

  useEffect(() => {
    void loadLatestFeature();
  }, [loadLatestFeature]);

  const sections = useMemo(
    () => (latestFeature ? buildSections(latestFeature.data) : []),
    [latestFeature]
  );
  const metadata = useMemo(
    () => (latestFeature ? extractMetadata(latestFeature) : null),
    [latestFeature]
  );

  if (viewState === "loading") {
    return <LoadingState message="Loading latest feature snapshot..." />;
  }

  if (viewState === "empty") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Dashboard</Text>
        <EmptyState message="No feature data available yet. Request a capture to generate your first snapshot." />
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Dashboard</Text>
        <ErrorState message={errorMessage ?? "Failed to load dashboard data."} />
        <Pressable accessibilityRole="button" onPress={loadLatestFeature} style={styles.retryButton}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  if (!latestFeature || !metadata) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>
      <Text style={styles.description}>
        Latest fulfilled feature snapshot grouped into readable sections.
      </Text>
      <Pressable accessibilityRole="button" onPress={loadLatestFeature} style={styles.refreshButton}>
        <Text style={styles.refreshButtonText}>Refresh Snapshot</Text>
      </Pressable>

      {sections.map((section) => (
        <FeatureSectionCard key={section.title} rows={section.rows} title={section.title} />
      ))}

      <FeatureMetadataCard metadata={metadata} />

      <Pressable
        accessibilityRole="button"
        onPress={() => navigation.navigate("FeatureDetail", { id: latestFeature.id })}
        style={styles.detailButton}
      >
        <Text style={styles.detailButtonText}>View Full Feature Details</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8
  },
  title: {
    color: "#111827",
    fontSize: 24,
    fontWeight: "700"
  },
  description: {
    color: "#4b5563",
    fontSize: 16
  },
  refreshButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  refreshButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
  },
  detailButton: {
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  detailButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center"
  },
  retryButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  retryButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
  }
});
