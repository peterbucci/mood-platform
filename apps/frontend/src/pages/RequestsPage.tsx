import { useCallback, useMemo, useState } from "react";
import { useIsFocused, useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import CreateRequestCard from "../components/requests/CreateRequestCard";
import EmptyRequestsState from "../components/requests/EmptyRequestsState";
import RequestList from "../components/requests/RequestList";
import RequestSummaryCard from "../components/requests/RequestSummaryCard";
import AppButton from "../components/ui/AppButton";
import AppCard from "../components/ui/AppCard";
import InfoText from "../components/ui/InfoText";
import { DEFAULT_REQUEST_POLL_INTERVAL_MS, useRequestPolling } from "../hooks/useRequestPolling";
import type { RootStackParamList } from "../router/AppRouter";
import { colors, radius, spacing, typography } from "../theme";
import type { FeatureRequestRecord } from "../types/requests";
import type { MoodCategory, MoodLabelValue } from "../types/mood";
import { getMoodDisplayModel } from "../utils/moodFormatting";
import { formatRequestRelativeTime, isSameLocalDay } from "../utils/requestFormatting";

function pluralizeCapture(count: number): string {
  return count === 1 ? "capture" : "captures";
}

function queueStatusMessage(pendingCount: number): string {
  if (pendingCount > 0) {
    return `${pendingCount} ${pluralizeCapture(pendingCount)} ${pendingCount === 1 ? "is" : "are"} processing. Updates appear automatically.`;
  }

  return "Queue is up to date.";
}

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
    isRefreshing,
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

  const nowMs = Date.now();
  const completedTodayCount = useMemo(
    () =>
      requestsWithMood.filter(
        (request) => request.status === "fulfilled" && isSameLocalDay(request.createdAt, nowMs)
      ).length,
    [nowMs, requestsWithMood]
  );
  const latestFulfilledRequest = useMemo(
    () => requestsWithMood.find((request) => request.status === "fulfilled") ?? null,
    [requestsWithMood]
  );
  const latestCaptureMood = latestFulfilledRequest
    ? getMoodDisplayModel(latestFulfilledRequest.label).text
    : "No completed captures yet";

  const pendingValue = isInitialLoading ? "--" : String(pendingCount);
  const completedTodayValue = isInitialLoading ? "--" : String(completedTodayCount);
  const lastCaptureValue = isInitialLoading
    ? "Loading"
    : latestFulfilledRequest
      ? formatRequestRelativeTime(latestFulfilledRequest.createdAt, nowMs)
      : "No captures";
  const historyStatusText =
    pendingCount > 0 ? "Capture in progress" : requestsWithMood.length > 0 ? "Recent activity" : "Waiting for your first capture";

  return (
    <View style={styles.container}>
      <View style={styles.pageHeader}>
        <View style={styles.pageHeaderCopy}>
          <Text style={styles.pageTitle}>Requests</Text>
          <Text style={styles.pageSubtitle}>
            Queue new captures, check what is in progress, and review recent snapshot activity.
          </Text>
        </View>
        <Pressable
          accessibilityRole="button"
          disabled={isRefreshing || isInitialLoading}
          onPress={() => void refresh()}
          style={[styles.refreshButton, isRefreshing || isInitialLoading ? styles.refreshButtonDisabled : null]}
          testID="requests-refresh-button"
        >
          <Text style={styles.refreshButtonText}>{isRefreshing ? "Refreshing..." : "Refresh"}</Text>
        </Pressable>
      </View>

      <View style={styles.summaryGrid}>
        <View style={styles.summaryHalf}>
          <RequestSummaryCard
            detail={pendingCount > 0 ? "Capture in progress" : "No pending captures"}
            label="Pending"
            tone={pendingCount > 0 ? "warning" : "neutral"}
            value={pendingValue}
          />
        </View>
        <View style={styles.summaryHalf}>
          <RequestSummaryCard
            detail={completedTodayCount > 0 ? "Ready to review" : "Nothing completed today"}
            label="Completed today"
            tone={completedTodayCount > 0 ? "success" : "neutral"}
            value={completedTodayValue}
          />
        </View>
        <View style={styles.summaryFull}>
          <RequestSummaryCard
            detail={latestCaptureMood}
            label="Last capture"
            tone={latestFulfilledRequest ? "info" : "neutral"}
            value={lastCaptureValue}
          />
        </View>
      </View>

      <View
        style={[
          styles.queueBanner,
          pendingCount > 0 ? styles.queueBannerActive : null
        ]}
      >
        <InfoText tone={pendingCount > 0 ? "warning" : "muted"}>{queueStatusMessage(pendingCount)}</InfoText>
      </View>

      <CreateRequestCard onCreated={handleRequestCreated} />

      <AppCard style={styles.historyCard}>
        <View style={styles.sectionHeader}>
          <View style={styles.sectionHeaderCopy}>
            <Text style={styles.sectionTitle}>Recent captures</Text>
            <Text style={styles.sectionSubtitle}>
              Capture queue activity and completed snapshot history.
            </Text>
          </View>
          <Text style={styles.sectionStatus}>{historyStatusText}</Text>
        </View>

        {isInitialLoading ? (
          <View style={styles.inlineState}>
            <ActivityIndicator color={colors.primary} size="small" />
            <InfoText tone="helper">Loading recent captures...</InfoText>
          </View>
        ) : null}

        {!isInitialLoading && errorMessage && requestsWithMood.length === 0 ? (
          <View style={styles.inlineState}>
            <Text style={styles.errorTitle}>Unable to load recent captures</Text>
            <InfoText tone="danger">{errorMessage}</InfoText>
            <AppButton label="Try Again" onPress={() => void refresh()} style={styles.inlineButton} variant="neutral" />
          </View>
        ) : null}

        {!isInitialLoading && !errorMessage && requestsWithMood.length === 0 ? <EmptyRequestsState /> : null}

        {!isInitialLoading && requestsWithMood.length > 0 ? (
          <>
            {errorMessage ? (
              <InfoText tone="warning">Showing your latest activity. Refresh to check for new updates.</InfoText>
            ) : null}
            <RequestList
              cancelErrorById={cancelErrorById}
              cancelingById={cancelingById}
              onPressCancel={handleCancelRequest}
              onPressFeature={handleOpenFeature}
              requests={requestsWithMood}
            />
          </>
        ) : null}
      </AppCard>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg
  },
  errorTitle: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  historyCard: {
    gap: spacing.md
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 128
  },
  inlineState: {
    gap: spacing.xs,
    minHeight: 96,
    justifyContent: "center"
  },
  pageHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  pageHeaderCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  pageSubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  pageTitle: {
    ...typography.title,
    color: colors.textPrimary
  },
  queueBanner: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  queueBannerActive: {
    backgroundColor: colors.warningSurface,
    borderColor: colors.warningBorder
  },
  refreshButton: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 34,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  refreshButtonDisabled: {
    opacity: 0.6
  },
  refreshButtonText: {
    ...typography.helper,
    color: colors.textPrimary,
    fontWeight: "700"
  },
  sectionHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  sectionHeaderCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  sectionStatus: {
    ...typography.helper,
    color: colors.textMuted,
    textAlign: "right"
  },
  sectionSubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  sectionTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  summaryGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  summaryFull: {
    width: "100%"
  },
  summaryHalf: {
    width: "48%"
  }
});
