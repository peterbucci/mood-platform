import { useCallback, useEffect, useState } from "react";
import { useIsFocused } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { StyleSheet, View } from "react-native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { isApiError } from "../api/errors";
import MoodLabelEditor from "../components/mood/MoodLabelEditor";
import MoodLabelCard from "../components/mood/MoodLabelCard";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppCard from "../components/ui/AppCard";
import AppButton from "../components/ui/AppButton";
import InfoText from "../components/ui/InfoText";
import SectionHeader from "../components/ui/SectionHeader";
import { useAppRefreshListener } from "../hooks/useAppRefresh";
import type { RootStackParamList } from "../router/AppRouter";
import { spacing } from "../theme";
import type { MoodCategory, MoodLabelValue } from "../types/mood";

type FeatureMoodLabelPageProps = NativeStackScreenProps<RootStackParamList, "FeatureMoodLabel">;
type MoodEditorViewState = "loading" | "ready" | "not_found" | "error";

export default function FeatureMoodLabelPage({ navigation, route }: FeatureMoodLabelPageProps) {
  const { id } = route.params;
  const isFocused = useIsFocused();
  const [viewState, setViewState] = useState<MoodEditorViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [initialLabel, setInitialLabel] = useState<MoodLabelValue>(undefined);

  const loadFeature = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);

    try {
      const feature = await getFeatureById(id);
      setInitialLabel(feature.label);
      setViewState("ready");
    } catch (error) {
      if (isApiError(error) && error.status === 404) {
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

  useAppRefreshListener(() => {
    if (!isFocused) {
      return;
    }
    void loadFeature();
  });

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

  if (viewState === "loading") {
    return <LoadingState message="Loading mood label editor..." />;
  }

  if (viewState === "not_found") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Update Mood Label" />
        <AppCard tone="subtle" style={styles.panel}>
          <EmptyState message={`Feature ${id} was not found.`} />
          <AppButton label="Cancel" onPress={handleBack} style={styles.inlineButton} variant="neutral" />
        </AppCard>
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Update Mood Label" />
        <AppCard tone="danger" style={styles.panel}>
          <ErrorState message={errorMessage ?? "Failed to load mood label editor."} />
          <View style={styles.actions}>
            <AppButton label="Try Again" onPress={loadFeature} style={styles.inlineButton} variant="neutral" />
            <AppButton label="Cancel" onPress={handleBack} style={styles.inlineButton} variant="neutral" />
          </View>
        </AppCard>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionHeader title="Update Mood Label" subtitle="Pick the mood that best matches this snapshot." />

      <AppCard tone="info" style={styles.panel}>
        <InfoText tone="helper">Feature Snapshot</InfoText>
        <InfoText>{id}</InfoText>
        <InfoText tone="helper">
          Choose one category and one emotion, then save to link this label to the feature.
        </InfoText>
      </AppCard>

      <MoodLabelCard label={initialLabel} />
      <MoodLabelEditor initialLabel={initialLabel} onCancel={handleBack} onSaveLabel={handleSaveLabel} showTitle={false} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  panel: {
    gap: spacing.sm
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 96
  }
});
