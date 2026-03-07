import type {
  CreateFeatureRequestInput,
  CreateFeatureRequestResponse,
  FeatureRequestRecord,
  PendingRequestCountResponse,
  RequestListResponse
} from "../types/requests";
import { apiDelete, apiGet, apiPost } from "./client";
import { createApiError } from "./errors";

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

export async function createFeatureRequest(
  input?: CreateFeatureRequestInput
): Promise<CreateFeatureRequestResponse> {
  const body =
    input && Object.prototype.hasOwnProperty.call(input, "clientFeatures")
      ? { clientFeatures: input.clientFeatures ?? null }
      : undefined;
  const payload = await apiPost<Partial<CreateFeatureRequestResponse>>("/features/request", body);

  const status = parseRequestStatus(payload?.status);
  if (!payload || typeof payload.requestId !== "string" || status === null) {
    throw createApiError({ message: "Invalid create feature request payload." });
  }

  return {
    requestId: payload.requestId,
    status
  };
}

export async function getRequests(limit = 20, offset = 0): Promise<FeatureRequestRecord[]> {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const queriedPayload = await apiGet<Partial<RequestListResponse>>(`/requests?${query.toString()}`);

  if (!queriedPayload || !Array.isArray(queriedPayload.items)) {
    throw createApiError({ message: "Invalid request list payload." });
  }

  return queriedPayload.items
    .map((item) => toRequestRecord(item))
    .filter((item): item is FeatureRequestRecord => item !== null);
}

export async function getPendingRequestCount(): Promise<number> {
  const payload = await apiGet<Partial<PendingRequestCountResponse>>("/requests/pending/count");

  if (!payload || typeof payload.pendingCount !== "number") {
    throw createApiError({ message: "Invalid pending request count payload." });
  }

  return payload.pendingCount;
}

export async function cancelRequest(requestId: string): Promise<FeatureRequestRecord> {
  const payload = await apiDelete<Partial<FeatureRequestRecord>>(`/requests/${requestId}`);
  const record = toRequestRecord(payload);
  if (!record) {
    throw createApiError({ message: "Invalid cancel request payload." });
  }
  return record;
}
