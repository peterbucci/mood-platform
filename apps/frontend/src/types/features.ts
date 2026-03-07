export type FeatureData = Record<string, unknown>;

export type FeatureRecord = {
  id: string;
  userId: string;
  createdAt: number;
  source: string;
  data: FeatureData;
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
