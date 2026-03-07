import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { cancelRequest, getPendingRequestCount, getRequests } from "../api/requests";
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
  cancelErrorById: Record<string, string>;
  cancelPendingRequest: (requestId: string) => Promise<void>;
  cancelingById: Record<string, boolean>;
  requests: FeatureRequestRecord[];
  pendingCount: number;
  errorMessage: string | null;
  isInitialLoading: boolean;
  isPolling: boolean;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
};

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

export function useRequestPolling({
  enabled = true,
  limit = 20,
  offset = 0,
  pollIntervalMs = DEFAULT_REQUEST_POLL_INTERVAL_MS
}: UseRequestPollingOptions = {}): UseRequestPollingResult {
  const [cancelErrorById, setCancelErrorById] = useState<Record<string, string>>({});
  const [cancelingById, setCancelingById] = useState<Record<string, boolean>>({});
  const [requests, setRequests] = useState<FeatureRequestRecord[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  const inFlightRef = useRef(false);
  const cancelingByIdRef = useRef<Record<string, boolean>>({});

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
        const [nextRequests, nextPendingCount] = await Promise.all([
          getRequests(limit, offset),
          getPendingRequestCount()
        ]);
        setRequests(dedupeRequestsById(nextRequests));
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

  const cancelPendingRequest = useCallback(async (requestId: string) => {
    if (cancelingByIdRef.current[requestId]) {
      return;
    }
    cancelingByIdRef.current[requestId] = true;
    setCancelingById((current) => ({
      ...current,
      [requestId]: true
    }));

    setCancelErrorById((current) => {
      if (!current[requestId]) {
        return current;
      }
      const next = { ...current };
      delete next[requestId];
      return next;
    });

    try {
      const canceledRequest = await cancelRequest(requestId);
      setRequests((current) =>
        dedupeRequestsById(
          current.map((request) => (request.id === requestId ? canceledRequest : request))
        )
      );
      setPendingCount((current) => Math.max(0, current - 1));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to cancel request.";
      setCancelErrorById((current) => ({
        ...current,
        [requestId]: message
      }));
    } finally {
      delete cancelingByIdRef.current[requestId];
      setCancelingById((current) => {
        const next = { ...current };
        delete next[requestId];
        return next;
      });
    }
  }, []);

  return {
    cancelErrorById,
    cancelPendingRequest,
    cancelingById,
    requests,
    pendingCount,
    errorMessage,
    isInitialLoading,
    isPolling,
    isRefreshing,
    refresh
  };
}
