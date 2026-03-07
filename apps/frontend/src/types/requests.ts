import type { MoodLabelValue } from "./mood";

export type RequestStatus = "pending" | "fulfilled" | "canceled";

export type CreateFeatureRequestInput = {
  clientFeatures?: Record<string, unknown> | null;
};

export type FeatureRequestRecord = {
  id: string;
  userId: string;
  createdAt: number;
  status: RequestStatus;
  featureId: string | null;
  source: string;
  label?: MoodLabelValue;
};

export type CreateFeatureRequestResponse = {
  requestId: string;
  status: RequestStatus;
};

export type DeleteRequestResponse = {
  id: string;
};

export type RequestListResponse = {
  items: FeatureRequestRecord[];
  limit: number;
  offset: number;
};

export type PendingRequestCountResponse = {
  pendingCount: number;
};
