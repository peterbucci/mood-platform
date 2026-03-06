export type RequestStatus = "pending" | "fulfilled" | "canceled";

export type FeatureRequestRecord = {
  id: string;
  userId: string;
  createdAt: number;
  status: RequestStatus;
  featureId: string | null;
  source: string;
};

export type CreateFeatureRequestResponse = {
  requestId: string;
  status: RequestStatus;
};

export type RequestListResponse = {
  items: FeatureRequestRecord[];
  limit: number;
  offset: number;
};

export type PendingRequestCountResponse = {
  pendingCount: number;
};
