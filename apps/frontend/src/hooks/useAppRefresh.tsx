import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

type RefreshListener = () => void | Promise<void>;

type AppRefreshContextValue = {
  isRefreshing: boolean;
  subscribe: (listener: RefreshListener) => () => void;
  triggerRefresh: () => void;
};

const NOOP_UNSUBSCRIBE = () => {};
const NOOP_CONTEXT: AppRefreshContextValue = {
  isRefreshing: false,
  subscribe: () => NOOP_UNSUBSCRIBE,
  triggerRefresh: () => {}
};

const AppRefreshContext = createContext<AppRefreshContextValue>(NOOP_CONTEXT);
const MIN_REFRESH_FEEDBACK_MS = 500;

type AppRefreshProviderProps = {
  children: ReactNode;
};

export function AppRefreshProvider({ children }: AppRefreshProviderProps) {
  const listenersRef = useRef(new Set<RefreshListener>());
  const inFlightRef = useRef(false);
  const feedbackTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    return () => {
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }
    };
  }, []);

  const subscribe = useCallback((listener: RefreshListener) => {
    listenersRef.current.add(listener);
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  const triggerRefresh = useCallback(() => {
    if (inFlightRef.current) {
      return;
    }

    inFlightRef.current = true;
    setIsRefreshing(true);
    const startedAt = Date.now();
    const listeners = Array.from(listenersRef.current);

    void Promise.allSettled(
      listeners.map(async (listener) => {
        await listener();
      })
    ).finally(() => {
      const elapsedMs = Date.now() - startedAt;
      const remainingMs = Math.max(0, MIN_REFRESH_FEEDBACK_MS - elapsedMs);

      feedbackTimeoutRef.current = setTimeout(() => {
        setIsRefreshing(false);
        inFlightRef.current = false;
      }, remainingMs);
    });
  }, []);

  const value = useMemo(
    () => ({
      isRefreshing,
      subscribe,
      triggerRefresh
    }),
    [isRefreshing, subscribe, triggerRefresh]
  );

  return <AppRefreshContext.Provider value={value}>{children}</AppRefreshContext.Provider>;
}

export function useAppRefresh() {
  return useContext(AppRefreshContext);
}

export function useAppRefreshListener(listener: RefreshListener) {
  const { subscribe } = useAppRefresh();
  const listenerRef = useRef(listener);
  listenerRef.current = listener;

  useEffect(
    () =>
      subscribe(() => {
        const currentListener = listenerRef.current;
        return currentListener();
      }),
    [subscribe]
  );
}
