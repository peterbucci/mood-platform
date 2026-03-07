import { useCallback, useEffect, useMemo, useState } from "react";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { isApiError } from "../api/errors";
import FeatureMetadataCard from "../components/features/FeatureMetadataCard";
import FeatureSectionCard from "../components/features/FeatureSectionCard";
import RawJsonToggle from "../components/features/RawJsonToggle";
import MoodLabelEditor from "../components/mood/MoodLabelEditor";
import MoodLabelCard from "../components/mood/MoodLabelCard";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import type { MoodCategory } from "../types/mood";
import { buildFeatureSections, extractFeatureMetadata } from "../utils/featureFormatting";

type FeatureDetailPageProps = NativeStackScreenProps<RootStackParamList, "FeatureDetail">;
type DetailViewState = "loading" | "ready" | "not_found" | "error";

export default function FeatureDetailPage({ route }: FeatureDetailPageProps) {
  const { id } = route.params;
  const [feature, setFeature] = useState<FeatureRecord | null>(null);
  const [viewState, setViewState] = useState<DetailViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadFeatureDetail = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);
    try {
      const record = await getFeatureById(id);
      setFeature(record);
      setViewState("ready");
    } catch (error) {
      if (isApiError(error) && error.status === 404) {
        setFeature(null);
        setViewState("not_found");
        return;
      }

      const message = error instanceof Error ? error.message : "Failed to load feature detail.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, [id]);

  useEffect(() => {
    void loadFeatureDetail();
  }, [loadFeatureDetail]);

  const metadata = useMemo(() => (feature ? extractFeatureMetadata(feature) : null), [feature]);
  const sections = useMemo(() => (feature ? buildFeatureSections(feature.data) : []), [feature]);

  const handleSaveMoodLabel = useCallback(
    async (category: MoodCategory, emotion: string) => {
      const nextLabel = await setFeatureLabel(id, category, emotion);
      setFeature((current) =>
        current
          ? {
              ...current,
              label: nextLabel
            }
          : current
      );
    },
    [id]
  );

  if (viewState === "loading") {
    return <LoadingState message="Loading feature detail..." />;
  }

  if (viewState === "not_found") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Feature Detail</Text>
        <EmptyState message={`Feature ${id} was not found.`} />
      </View>
    );
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Feature Detail</Text>
        <ErrorState message={errorMessage ?? "Failed to load feature detail."} />
        <Pressable accessibilityRole="button" onPress={loadFeatureDetail} style={styles.retryButton}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  if (!feature || !metadata) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Feature Detail</Text>
      <Text style={styles.description}>Readable breakdown for feature snapshot {id}.</Text>
      <MoodLabelCard label={feature.label} />
      <MoodLabelEditor initialLabel={feature.label} onSaveLabel={handleSaveMoodLabel} />
      <FeatureMetadataCard metadata={metadata} />
      {sections.map((section) => (
        <FeatureSectionCard key={section.title} rows={section.rows} title={section.title} />
      ))}
      <RawJsonToggle payload={feature} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8
  },
  title: {
    color: "#111827",
    fontSize: 24,
    fontWeight: "700"
  },
  description: {
    color: "#4b5563",
    fontSize: 16
  },
  retryButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  retryButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
  }
});
