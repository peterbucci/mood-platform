import { useCallback, useEffect, useMemo, useState } from "react";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { StyleSheet, View } from "react-native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { isApiError } from "../api/errors";
import FeatureSnapshotCard from "../components/mood/FeatureSnapshotCard";
import MoodLabelEditor from "../components/mood/MoodLabelEditor";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppCard from "../components/ui/AppCard";
import AppButton from "../components/ui/AppButton";
import SectionHeader from "../components/ui/SectionHeader";
import type { RootStackParamList } from "../router/AppRouter";
import { spacing } from "../theme";
import type { FeatureRecord } from "../types/features";
import type { MoodCategory } from "../types/mood";
import { shortenFeatureId } from "../utils/featureHistoryFormatting";
import { formatFeatureSourceLabel, formatTimestamp } from "../utils/featureFormatting";

type FeatureMoodLabelPageProps = NativeStackScreenProps<RootStackParamList, "FeatureMoodLabel">;
type MoodEditorViewState = "loading" | "ready" | "not_found" | "error";

export default function FeatureMoodLabelPage({ navigation, route }: FeatureMoodLabelPageProps) {
  const { id } = route.params;
  const [viewState, setViewState] = useState<MoodEditorViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feature, setFeature] = useState<FeatureRecord | null>(null);

  const loadFeature = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);

    try {
      const featureRecord = await getFeatureById(id);
      setFeature(featureRecord);
      setViewState("ready");
    } catch (error) {
      if (isApiError(error) && error.status === 404) {
        setFeature(null);
        setViewState("not_found");
        return;
      }

      const message = error instanceof Error ? error.message : "Failed to load mood label editor.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, [id]);

  useEffect(() => {
    void loadFeature();
  }, [loadFeature]);

  const handleBack = useCallback(() => {
    navigation.goBack();
  }, [navigation]);

  const handleSaveLabel = useCallback(
    async (category: MoodCategory, emotion: string) => {
      await setFeatureLabel(id, category, emotion);
      navigation.navigate("FeatureDetail", { id, refreshAt: Date.now() });
    },
    [id, navigation]
  );

  const snapshotReference = useMemo(() => (feature ? shortenFeatureId(feature.id) : shortenFeatureId(id)), [feature, id]);
  const captureText = feature ? `Captured ${formatTimestamp(feature.createdAt)}` : null;
  const sourceLabel = feature ? formatFeatureSourceLabel(feature.source) : null;

  if (viewState === "loading") {
    return <LoadingState message="Loading mood label editor..." />;
  }

  if (viewState === "not_found") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Update Mood Label" subtitle="Choose the mood that best matches this snapshot." />
        <AppCard tone="subtle" style={styles.panel}>
          <EmptyState message={`Feature ${id} was not found.`} />
          <AppButton label="Cancel" onPress={handleBack} style={styles.inlineButton} variant="outline" />
        </AppCard>
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Update Mood Label" subtitle="Choose the mood that best matches this snapshot." />
        <AppCard tone="danger" style={styles.panel}>
          <ErrorState message={errorMessage ?? "Failed to load mood label editor."} />
          <View style={styles.actions}>
            <AppButton label="Try Again" onPress={loadFeature} style={styles.inlineButton} />
            <AppButton label="Cancel" onPress={handleBack} style={styles.inlineButton} variant="outline" />
          </View>
        </AppCard>
      </View>
    );
  }

  if (!feature) {
    return null;
  }

  return (
    <View style={styles.container}>
      <SectionHeader
        title="Update Mood Label"
        subtitle="Choose the mood that best matches this snapshot."
      />

      <FeatureSnapshotCard
        capturedAt={captureText}
        featureId={snapshotReference}
        helperText="This label helps connect the snapshot to how you felt when it was captured."
        sourceLabel={sourceLabel}
      />

      <MoodLabelEditor
        initialLabel={feature.label}
        onCancel={handleBack}
        onSaveLabel={handleSaveLabel}
        showTitle={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  container: {
    gap: spacing.md
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 96
  },
  panel: {
    gap: spacing.sm
  }
});
