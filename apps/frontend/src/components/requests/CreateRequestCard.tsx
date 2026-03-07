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

type CreateRequestCardProps = {
  onCreated?: (request: CreateFeatureRequestResponse) => Promise<void> | void;
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

    try {
      const created = await createFeatureRequest({
        clientFeatures: {
          moodCategory: selectedCategory,
          moodEmotion: selectedEmotion
        }
      });
      setLatestCreated(created);
      if (onCreated) {
        await onCreated(created);
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
    <AppCard tone="info" style={styles.card}>
      <Text style={styles.title}>Log Emotion + Capture Features</Text>
      <InfoText tone="helper">
        Choose how you feel right now, then submit a feature capture request. The request is queued
        immediately.
      </InfoText>
      <CategorySelector
        disabled={isSubmitting}
        onSelectCategory={handleSelectCategory}
        selectedCategory={selectedCategory}
      />
      <EmotionSelector
        category={selectedCategory}
        disabled={isSubmitting || !selectedCategory}
        onSelectEmotion={handleSelectEmotion}
        selectedEmotion={selectedEmotion}
      />
      <AppButton
        disabled={isSubmitting || !selectedCategory || !selectedEmotion}
        isLoading={isSubmitting}
        label="Log Emotion"
        onPress={handleCreate}
        testID="log-emotion-button"
      />
      {latestCreated ? (
        <AppCard tone="success">
          <Text style={styles.successTitle}>Emotion logged and request created</Text>
          <InfoText tone="success">Request ID: {latestCreated.requestId}</InfoText>
          <InfoText tone="success">Status: {latestCreated.status}</InfoText>
          <InfoText tone="success">
            Mood: {selectedCategory} / {selectedEmotion}
          </InfoText>
        </AppCard>
      ) : null}
      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.sm
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  },
  successTitle: {
    ...typography.bodyStrong,
    color: colors.successText
  },
  errorText: {
    ...typography.bodyStrong,
    color: colors.dangerText
  }
});
