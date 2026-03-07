import { useCallback, useEffect, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { getFeatures } from "../api/features";
import FeatureList from "../components/features/FeatureList";
import EmptyState from "../components/states/EmptyState";
import ErrorState from "../components/states/ErrorState";
import LoadingState from "../components/states/LoadingState";
import type { RootStackParamList } from "../router/AppRouter";
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
        <Text style={styles.title}>Features</Text>
        <ErrorState message={errorMessage ?? "Failed to load feature history."} />
        <Pressable accessibilityRole="button" onPress={loadFeatures} style={styles.retryButton}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  if (viewState === "empty") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Features</Text>
        <Text style={styles.description}>Browse previously generated feature captures.</Text>
        <EmptyState message="No feature captures yet" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Features</Text>
      <Text style={styles.description}>Browse previously generated feature captures.</Text>
      <Pressable accessibilityRole="button" onPress={loadFeatures} style={styles.refreshButton}>
        <Text style={styles.refreshButtonText}>Refresh History</Text>
      </Pressable>
      <FeatureList features={features} onPressFeature={handleOpenFeature} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  refreshButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  refreshButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
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
