import { useCallback, useEffect, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { StyleSheet, View } from "react-native";

import { getFeatures } from "../api/features";
import FeatureList from "../components/features/FeatureList";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import AppButton from "../components/ui/AppButton";
import SectionHeader from "../components/ui/SectionHeader";
import type { RootStackParamList } from "../router/AppRouter";
import { spacing } from "../theme";
import type { FeatureRecord } from "../types/features";

type FeaturesViewState = "loading" | "ready" | "empty" | "error";

export default function FeaturesPage() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [features, setFeatures] = useState<FeatureRecord[]>([]);
  const [viewState, setViewState] = useState<FeaturesViewState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadFeatures = useCallback(async () => {
    setViewState("loading");
    setErrorMessage(null);

    try {
      const records = await getFeatures();
      setFeatures(records);
      setViewState(records.length > 0 ? "ready" : "empty");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load feature history.";
      setErrorMessage(message);
      setViewState("error");
    }
  }, []);

  useEffect(() => {
    void loadFeatures();
  }, [loadFeatures]);

  const handleOpenFeature = useCallback(
    (featureId: string) => {
      navigation.navigate("FeatureDetail", { id: featureId });
    },
    [navigation]
  );

  if (viewState === "loading") {
    return <LoadingState message="Loading feature history..." />;
  }

  if (viewState === "error") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Features" />
        <ErrorState message={errorMessage ?? "Failed to load feature history."} />
        <AppButton label="Try Again" onPress={loadFeatures} style={styles.inlineButton} variant="neutral" />
      </View>
    );
  }

  if (viewState === "empty") {
    return (
      <View style={styles.container}>
        <SectionHeader title="Features" subtitle="Browse previous feature captures." />
        <EmptyState message="No feature captures yet. Request a capture to build your history." />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionHeader title="Features" subtitle="Browse previous feature captures." />
      <AppButton label="Refresh History" onPress={loadFeatures} style={styles.inlineButton} variant="neutral" />
      <FeatureList features={features} onPressFeature={handleOpenFeature} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    gap: spacing.sm
  },
  inlineButton: {
    alignSelf: "flex-start",
    minWidth: 144
  }
});
