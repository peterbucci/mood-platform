import { useCallback, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { createFeatureRequest } from "../../api/requests";
import { colors, spacing, typography } from "../../theme";
import CategorySelector from "../mood/CategorySelector";
import EmotionSelector from "../mood/EmotionSelector";
import type { CreateFeatureRequestResponse } from "../../types/requests";
import type { MoodCategory } from "../../types/mood";
import { getDefaultEmotionForCategory, isValidEmotionForCategory } from "../../utils/moodTaxonomy";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type MoodSelection = {
  category: MoodCategory;
  emotion: string;
};

type CreateRequestCardProps = {
  onCreated?: (request: CreateFeatureRequestResponse, moodSelection: MoodSelection) => Promise<void> | void;
};

const DEFAULT_ERROR_MESSAGE = "Unable to create request right now.";

export default function CreateRequestCard({ onCreated }: CreateRequestCardProps) {
  const [selectedCategory, setSelectedCategory] = useState<MoodCategory | null>(null);
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latestCreated, setLatestCreated] = useState<CreateFeatureRequestResponse | null>(null);
  const inFlightRef = useRef(false);

  const handleSelectCategory = useCallback((category: MoodCategory) => {
    setSelectedCategory(category);
    setLatestCreated(null);
    setSelectedEmotion((current) => {
      if (current && isValidEmotionForCategory(category, current)) {
        return current;
      }
      return getDefaultEmotionForCategory(category);
    });
    setErrorMessage(null);
  }, []);

  const handleSelectEmotion = useCallback((emotion: string) => {
    setSelectedEmotion(emotion);
    setLatestCreated(null);
    setErrorMessage(null);
  }, []);

  const handleCreate = useCallback(async () => {
    if (inFlightRef.current || !selectedCategory || !selectedEmotion) {
      if (!selectedCategory || !selectedEmotion) {
        setErrorMessage("Please select both category and emotion.");
      }
      return;
    }
    inFlightRef.current = true;
    setIsSubmitting(true);
    setErrorMessage(null);
    setLatestCreated(null);

    try {
      const created = await createFeatureRequest({
        clientFeatures: {
          moodCategory: selectedCategory,
          moodEmotion: selectedEmotion
        }
      });
      setLatestCreated(created);
      if (onCreated) {
        await onCreated(created, {
          category: selectedCategory,
          emotion: selectedEmotion
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : DEFAULT_ERROR_MESSAGE;
      setErrorMessage(message);
    } finally {
      inFlightRef.current = false;
      setIsSubmitting(false);
    }
  }, [onCreated, selectedCategory, selectedEmotion]);

  return (
    <AppCard style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Capture a New Snapshot</Text>
        <InfoText tone="helper">Log how you feel and capture a new feature snapshot.</InfoText>
      </View>
      <CategorySelector
        disabled={isSubmitting}
        onSelectCategory={handleSelectCategory}
        selectedCategory={selectedCategory}
      />
      {selectedCategory ? (
        <View style={styles.emotionSection}>
          <InfoText tone="helper">Pick the emotion that fits best.</InfoText>
          <EmotionSelector
            category={selectedCategory}
            disabled={isSubmitting}
            onSelectEmotion={handleSelectEmotion}
            selectedEmotion={selectedEmotion}
          />
        </View>
      ) : (
        <InfoText tone="muted">Choose a category to see matching emotions.</InfoText>
      )}
      <AppButton
        disabled={isSubmitting || !selectedCategory || !selectedEmotion}
        isLoading={isSubmitting}
        label="Capture Snapshot"
        onPress={handleCreate}
        style={styles.actionButton}
        testID="log-emotion-button"
      />
      {latestCreated ? (
        <View style={styles.feedbackRow}>
          <Text style={styles.feedbackTitle}>
            {latestCreated.status === "pending" ? "Capture in progress" : "Snapshot queued"}
          </Text>
          <InfoText tone={latestCreated.status === "pending" ? "warning" : "success"}>
            Your request was added to the queue.
          </InfoText>
        </View>
      ) : null}
      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    alignSelf: "flex-start",
    minWidth: 168
  },
  card: {
    gap: spacing.sm
  },
  emotionSection: {
    gap: spacing.xs
  },
  feedbackRow: {
    backgroundColor: colors.warningSurface,
    borderColor: colors.warningBorder,
    borderRadius: 10,
    borderWidth: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  feedbackTitle: {
    ...typography.bodyStrong,
    color: colors.warningText
  },
  header: {
    gap: spacing.xxs
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  },
  errorText: {
    ...typography.bodyStrong,
    color: colors.dangerText
  }
});
