import type { MoodLabelValue } from "./mood";

export type FeatureData = Record<string, unknown>;
export type FeatureDataMap = FeatureData;

export type FeatureRecord = {
  id: string;
  userId: string;
  createdAt: number;
  source: string;
  data: FeatureData;
  label?: MoodLabelValue;
  summaryMetadata?: Record<string, unknown> | null;
  extractorVersion?: string | null;
  windowStart?: string | null;
  windowEnd?: string | null;
  sourceTimezone?: string | null;
};

export type FeatureListResponse = {
  items: FeatureRecord[];
  limit: number;
  offset: number;
};

export type FeatureDeleteResponse = {
  id: string;
};
