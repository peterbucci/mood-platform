import { useCallback, useMemo, useState } from "react";
import { useIsFocused, useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { StyleSheet, View } from "react-native";

import CreateRequestCard from "../components/requests/CreateRequestCard";
import PendingCountCard from "../components/requests/PendingCountCard";
import RequestList from "../components/requests/RequestList";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import InfoText from "../components/ui/InfoText";
import SectionHeader from "../components/ui/SectionHeader";
import { useAppRefreshListener } from "../hooks/useAppRefresh";
import { DEFAULT_REQUEST_POLL_INTERVAL_MS, useRequestPolling } from "../hooks/useRequestPolling";
import type { RootStackParamList } from "../router/AppRouter";
import { spacing } from "../theme";
import type { FeatureRequestRecord } from "../types/requests";
import type { MoodCategory, MoodLabelValue } from "../types/mood";

export default function RequestsPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const isFocused = useIsFocused();
  const [requestMoodById, setRequestMoodById] = useState<Record<string, MoodLabelValue>>({});
  const {
    cancelErrorById,
    cancelPendingRequest,
    cancelingById,
    requests,
    pendingCount,
    errorMessage,
    isInitialLoading,
    isPolling,
    refresh
  } = useRequestPolling({
    enabled: isFocused,
    pollIntervalMs: DEFAULT_REQUEST_POLL_INTERVAL_MS
  });

  const handleOpenFeature = useCallback(
    (featureId: string) => {
      navigation.navigate("FeatureDetail", { id: featureId });
    },
    [navigation]
  );

  const handleCancelRequest = useCallback(
    async (requestId: string) => {
      await cancelPendingRequest(requestId);
    },
    [cancelPendingRequest]
  );

  const handleRequestCreated = useCallback(
    async (
      created: { requestId: string },
      moodSelection: {
        category: MoodCategory;
        emotion: string;
      }
    ) => {
      setRequestMoodById((current) => ({
        ...current,
        [created.requestId]: {
          category: moodSelection.category,
          emotion: moodSelection.emotion
        }
      }));
      await refresh();
    },
    [refresh]
  );

  const requestsWithMood = useMemo<FeatureRequestRecord[]>(
    () =>
      requests.map((request) => {
        if (request.label) {
          return request;
        }

        const mood = requestMoodById[request.id];
        if (!mood) {
          return request;
        }

        return {
          ...request,
          label: mood
        };
      }),
    [requestMoodById, requests]
  );

  useAppRefreshListener(() => {
    if (!isFocused) {
      return;
    }
    void refresh();
  });

  return (
    <View style={styles.container}>
      <SectionHeader title="Requests" subtitle="Track feature capture requests and queue progress." />
      <CreateRequestCard onCreated={handleRequestCreated} />
      <PendingCountCard pendingCount={pendingCount} />
      {isPolling ? (
        <InfoText tone="warning">Auto-updating while requests are pending.</InfoText>
      ) : null}

      {isInitialLoading ? <LoadingState message="Loading requests..." /> : null}
      {!isInitialLoading && errorMessage && requestsWithMood.length === 0 ? (
        <View style={styles.errorContainer}>
          <ErrorState message={errorMessage} />
          <AppButton label="Try Again" onPress={refresh} style={styles.inlineButton} variant="neutral" />
        </View>
      ) : null}
      {!isInitialLoading && !errorMessage && requestsWithMood.length === 0 ? (
        <EmptyState message="No feature requests yet. Trigger a capture to get started." />
      ) : null}
      {requestsWithMood.length > 0 ? (
        <RequestList
          cancelErrorById={cancelErrorById}
          cancelingById={cancelingById}
          onPressCancel={handleCancelRequest}
          onPressFeature={handleOpenFeature}
          requests={requestsWithMood}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 128
  },
  errorContainer: {
    gap: spacing.sm
  }
});
