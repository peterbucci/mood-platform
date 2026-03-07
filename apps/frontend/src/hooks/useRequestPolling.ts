import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getFeatures } from "../api/features";
import { deleteRequest, getPendingRequestCount, getRequests } from "../api/requests";
import type { FeatureRequestRecord } from "../types/requests";

export const DEFAULT_REQUEST_POLL_INTERVAL_MS = 7000;

type RefreshMode = "initial" | "manual" | "poll";

type UseRequestPollingOptions = {
  enabled?: boolean;
  limit?: number;
  offset?: number;
  pollIntervalMs?: number;
};

type UseRequestPollingResult = {
  deleteErrorById: Record<string, string>;
  deleteRequestRecord: (requestId: string) => Promise<void>;
  deletingById: Record<string, boolean>;
  requests: FeatureRequestRecord[];
  pendingCount: number;
  errorMessage: string | null;
  isInitialLoading: boolean;
  isPolling: boolean;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
};

const DEFAULT_DELETE_ERROR_MESSAGE = "Unable to delete request. Please try again.";

function dedupeRequestsById(requests: FeatureRequestRecord[]): FeatureRequestRecord[] {
  const byId = new Map<string, FeatureRequestRecord>();
  for (const request of requests) {
    byId.set(request.id, request);
  }

  return Array.from(byId.values()).sort((a, b) => b.createdAt - a.createdAt);
}

function hasPendingRequests(requests: FeatureRequestRecord[], pendingCount: number): boolean {
  if (pendingCount > 0) {
    return true;
  }
  return requests.some((request) => request.status === "pending");
}

function mergeRequestLabelsFromFeatures(
  requests: FeatureRequestRecord[],
  features: Array<{ id: string; label?: FeatureRequestRecord["label"] }>
): FeatureRequestRecord[] {
  const labelByFeatureId = new Map<string, FeatureRequestRecord["label"]>();
  for (const feature of features) {
    if (feature.label) {
      labelByFeatureId.set(feature.id, feature.label);
    }
  }

  return requests.map((request) => {
    if (request.label || !request.featureId) {
      return request;
    }

    const label = labelByFeatureId.get(request.featureId);
    if (!label) {
      return request;
    }

    return {
      ...request,
      label
    };
  });
}

export function useRequestPolling({
  enabled = true,
  limit = 20,
  offset = 0,
  pollIntervalMs = DEFAULT_REQUEST_POLL_INTERVAL_MS
}: UseRequestPollingOptions = {}): UseRequestPollingResult {
  const [deleteErrorById, setDeleteErrorById] = useState<Record<string, string>>({});
  const [deletingById, setDeletingById] = useState<Record<string, boolean>>({});
  const [requests, setRequests] = useState<FeatureRequestRecord[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  const inFlightRef = useRef(false);
  const deletingByIdRef = useRef<Record<string, boolean>>({});

  const loadSnapshot = useCallback(
    async (mode: RefreshMode) => {
      if (!enabled || inFlightRef.current) {
        return;
      }

      inFlightRef.current = true;
      if (mode === "initial") {
        setIsInitialLoading(true);
      }
      if (mode === "manual") {
        setIsRefreshing(true);
      }

      try {
        const [nextRequests, nextPendingCount, nextFeatures] = await Promise.all([
          getRequests(limit, offset),
          getPendingRequestCount(),
          getFeatures(Math.max(limit, 100), 0).catch(() => [])
        ]);
        const requestsWithLabels = mergeRequestLabelsFromFeatures(nextRequests, nextFeatures);
        setRequests(dedupeRequestsById(requestsWithLabels));
        setPendingCount(nextPendingCount);
        setErrorMessage(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to load requests.";
        setErrorMessage(message);
      } finally {
        inFlightRef.current = false;
        if (mode === "initial") {
          setIsInitialLoading(false);
        }
        if (mode === "manual") {
          setIsRefreshing(false);
        }
      }
    },
    [enabled, limit, offset]
  );

  useEffect(() => {
    if (!enabled) {
      setIsPolling(false);
      setIsInitialLoading(false);
      setIsRefreshing(false);
      return;
    }

    void loadSnapshot("initial");
  }, [enabled, loadSnapshot]);

  const shouldPoll = useMemo(
    () => enabled && !isInitialLoading && hasPendingRequests(requests, pendingCount),
    [enabled, isInitialLoading, pendingCount, requests]
  );

  useEffect(() => {
    if (!shouldPoll) {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    const timer = setInterval(() => {
      void loadSnapshot("poll");
    }, pollIntervalMs);

    return () => {
      clearInterval(timer);
    };
  }, [loadSnapshot, pollIntervalMs, shouldPoll]);

  const refresh = useCallback(async () => {
    await loadSnapshot("manual");
  }, [loadSnapshot]);

  const deleteRequestRecord = useCallback(
    async (requestId: string) => {
      if (deletingByIdRef.current[requestId]) {
        return;
      }

      deletingByIdRef.current[requestId] = true;
      setDeletingById((current) => ({
        ...current,
        [requestId]: true
      }));

      setDeleteErrorById((current) => {
        if (!current[requestId]) {
          return current;
        }
        const next = { ...current };
        delete next[requestId];
        return next;
      });

      const deletedRequest = requests.find((request) => request.id === requestId) ?? null;

      try {
        await deleteRequest(requestId);
        setRequests((current) => current.filter((request) => request.id !== requestId));
        if (deletedRequest?.status === "pending") {
          setPendingCount((current) => Math.max(0, current - 1));
        }
        await loadSnapshot("manual");
      } catch {
        const message = DEFAULT_DELETE_ERROR_MESSAGE;
        setDeleteErrorById((current) => ({
          ...current,
          [requestId]: message
        }));
        throw new Error(message);
      } finally {
        delete deletingByIdRef.current[requestId];
        setDeletingById((current) => {
          const next = { ...current };
          delete next[requestId];
          return next;
        });
      }
    },
    [loadSnapshot, requests]
  );

  return {
    deleteErrorById,
    deleteRequestRecord,
    deletingById,
    requests,
    pendingCount,
    errorMessage,
    isInitialLoading,
    isPolling,
    isRefreshing,
    refresh
  };
}
