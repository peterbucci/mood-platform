import type { FeatureListResponse, FeatureRecord } from "../types/features";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

function getApiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, "");
  }
  return DEFAULT_API_BASE_URL;
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

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
    extractorVersion:
      typeof payload.extractorVersion === "string" ? payload.extractorVersion : null,
    windowStart: typeof payload.windowStart === "string" ? payload.windowStart : null,
    windowEnd: typeof payload.windowEnd === "string" ? payload.windowEnd : null,
    sourceTimezone: typeof payload.sourceTimezone === "string" ? payload.sourceTimezone : null
  };
}

export async function getLatestFeature(): Promise<FeatureRecord | null> {
  const response = await fetch(buildApiUrl("/features/latest"), {
    headers: {
      Accept: "application/json"
    }
  });

  if (response.status === 404) {
    return null;
  }

  const payload = await parseJson(response);
  if (!response.ok) {
    throw new Error("Failed to fetch latest feature snapshot.");
  }

  const record = toFeatureRecord(payload);
  if (!record) {
    throw new Error("Invalid latest feature payload.");
  }
  return record;
}

export async function getFeatureById(id: string): Promise<FeatureRecord> {
  const response = await fetch(buildApiUrl(`/features/${id}`), {
    headers: {
      Accept: "application/json"
    }
  });
  const payload = await parseJson(response);

  if (!response.ok) {
    throw new Error("Failed to fetch feature by id.");
  }

  const record = toFeatureRecord(payload);
  if (!record) {
    throw new Error("Invalid feature payload.");
  }
  return record;
}

export async function getFeatures(limit = 20, offset = 0): Promise<FeatureRecord[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  const response = await fetch(buildApiUrl(`/features?${query.toString()}`), {
    headers: {
      Accept: "application/json"
    }
  });
  const payload = (await parseJson(response)) as Partial<FeatureListResponse> | null;

  if (!response.ok) {
    throw new Error("Failed to fetch features.");
  }
  if (!payload || !Array.isArray(payload.items)) {
    throw new Error("Invalid feature list payload.");
  }

  return payload.items
    .map((item) => toFeatureRecord(item))
    .filter((item): item is FeatureRecord => item !== null);
}
