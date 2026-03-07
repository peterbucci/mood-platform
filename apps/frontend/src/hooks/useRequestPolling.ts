import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getPendingRequestCount, getRequests } from "../api/requests";
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
  const [requests, setRequests] = useState<FeatureRequestRecord[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPolling, setIsPolling] = useState(false);

  const inFlightRef = useRef(false);

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

  return {
    requests,
    pendingCount,
    errorMessage,
    isInitialLoading,
    isPolling,
    isRefreshing,
    refresh
  };
}
