import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from "react";

type RefreshListener = () => void | Promise<void>;

type AppRefreshContextValue = {
  subscribe: (listener: RefreshListener) => () => void;
  triggerRefresh: () => void;
};

const NOOP_UNSUBSCRIBE = () => {};
const NOOP_CONTEXT: AppRefreshContextValue = {
  subscribe: () => NOOP_UNSUBSCRIBE,
  triggerRefresh: () => {}
};

const AppRefreshContext = createContext<AppRefreshContextValue>(NOOP_CONTEXT);

type AppRefreshProviderProps = {
  children: ReactNode;
};

export function AppRefreshProvider({ children }: AppRefreshProviderProps) {
  const listenersRef = useRef(new Set<RefreshListener>());

  const subscribe = useCallback((listener: RefreshListener) => {
    listenersRef.current.add(listener);
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  const triggerRefresh = useCallback(() => {
    for (const listener of listenersRef.current) {
      void listener();
    }
  }, []);

  const value = useMemo(
    () => ({
      subscribe,
      triggerRefresh
    }),
    [subscribe, triggerRefresh]
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
