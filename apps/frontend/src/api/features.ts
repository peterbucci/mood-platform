import type { FeatureDeleteResponse, FeatureListResponse, FeatureRecord } from "../types/features";
import { apiDelete, apiGet } from "./client";
import { createApiError } from "./errors";

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function toFeatureRecord(payload: unknown): FeatureRecord | null {
  if (!isRecord(payload)) {
    return null;
  }
  const data = isRecord(payload.data) ? payload.data : null;
  if (
    typeof payload.id !== "string" ||
    typeof payload.userId !== "string" ||
    typeof payload.createdAt !== "number" ||
    typeof payload.source !== "string" ||
    data === null
  ) {
    return null;
  }
  return {
    id: payload.id,
    userId: payload.userId,
    createdAt: payload.createdAt,
    source: payload.source,
    data,
    summaryMetadata:
      isRecord(payload.summaryMetadata)
        ? payload.summaryMetadata
        : isRecord(payload.summary_metadata)
          ? payload.summary_metadata
          : null,
    extractorVersion:
      typeof payload.extractorVersion === "string" ? payload.extractorVersion : null,
    windowStart: typeof payload.windowStart === "string" ? payload.windowStart : null,
    windowEnd: typeof payload.windowEnd === "string" ? payload.windowEnd : null,
    sourceTimezone: typeof payload.sourceTimezone === "string" ? payload.sourceTimezone : null
  };
}

export async function getLatestFeature(): Promise<FeatureRecord | null> {
  const payload = await apiGet<unknown>("/features/latest", { allow404: true });
  if (payload === null) {
    return null;
  }

  const record = toFeatureRecord(payload);
  if (!record) {
    throw createApiError({ message: "Invalid latest feature payload." });
  }
  return record;
}

export async function getFeatureById(id: string): Promise<FeatureRecord> {
  const payload = await apiGet<unknown>(`/features/${id}`);

  const record = toFeatureRecord(payload);
  if (!record) {
    throw createApiError({ message: "Invalid feature payload." });
  }
  return record;
}

export async function getFeatures(limit = 20, offset = 0): Promise<FeatureRecord[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  const payload = await apiGet<Partial<FeatureListResponse>>(`/features?${query.toString()}`);
  if (!payload || !Array.isArray(payload.items)) {
    throw createApiError({ message: "Invalid feature list payload." });
  }

  return payload.items
    .map((item) => toFeatureRecord(item))
    .filter((item): item is FeatureRecord => item !== null);
}

export async function deleteFeature(featureId: string): Promise<FeatureDeleteResponse> {
  const payload = await apiDelete<Partial<FeatureDeleteResponse>>(`/features/${featureId}`);
  if (!payload || typeof payload.id !== "string") {
    throw createApiError({ message: "Invalid delete feature payload." });
  }
  return { id: payload.id };
}
