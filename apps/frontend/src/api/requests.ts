import type {
  CreateFeatureRequestResponse,
  FeatureRequestRecord,
  PendingRequestCountResponse,
  RequestListResponse
} from "../types/requests";

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

function parseRequestStatus(value: unknown): CreateFeatureRequestResponse["status"] | null {
  if (value === "pending" || value === "fulfilled" || value === "canceled") {
    return value;
  }
  return null;
}

function toRequestRecord(payload: unknown): FeatureRequestRecord | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const record = payload as Partial<FeatureRequestRecord>;
  const parsedStatus = parseRequestStatus(record.status);
  if (
    typeof record.id !== "string" ||
    typeof record.userId !== "string" ||
    typeof record.createdAt !== "number" ||
    parsedStatus === null ||
    typeof record.source !== "string"
  ) {
    return null;
  }
  return {
    id: record.id,
    userId: record.userId,
    createdAt: record.createdAt,
    status: parsedStatus,
    featureId: typeof record.featureId === "string" ? record.featureId : null,
    source: record.source
  };
}

export async function createFeatureRequest(): Promise<CreateFeatureRequestResponse> {
  const response = await fetch(buildApiUrl("/features/request"), {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  const payload = (await parseJson(response)) as Partial<CreateFeatureRequestResponse> | null;

  if (!response.ok) {
    throw new Error("Failed to create feature request.");
  }

  const status = parseRequestStatus(payload?.status);
  if (!payload || typeof payload.requestId !== "string" || status === null) {
    throw new Error("Invalid create feature request payload.");
  }

  return {
    requestId: payload.requestId,
    status
  };
}

export async function getRequests(limit = 20, offset = 0): Promise<FeatureRequestRecord[]> {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  const response = await fetch(buildApiUrl(`/requests?${query.toString()}`), {
    headers: {
      Accept: "application/json"
    }
  });
  const payload = (await parseJson(response)) as Partial<RequestListResponse> | null;

  if (!response.ok) {
    throw new Error("Failed to fetch feature requests.");
  }
  if (!payload || !Array.isArray(payload.items)) {
    throw new Error("Invalid request list payload.");
  }

  return payload.items
    .map((item) => toRequestRecord(item))
    .filter((item): item is FeatureRequestRecord => item !== null);
}

export async function getPendingRequestCount(): Promise<number> {
  const response = await fetch(buildApiUrl("/requests/pending/count"), {
    headers: {
      Accept: "application/json"
    }
  });
  const payload = (await parseJson(response)) as Partial<PendingRequestCountResponse> | null;

  if (!response.ok) {
    throw new Error("Failed to fetch pending request count.");
  }
  if (!payload || typeof payload.pendingCount !== "number") {
    throw new Error("Invalid pending request count payload.");
  }

  return payload.pendingCount;
}
