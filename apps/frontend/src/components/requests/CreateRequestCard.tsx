import { useCallback, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { createFeatureRequest } from "../../api/requests";
import CategorySelector from "../mood/CategorySelector";
import EmotionSelector from "../mood/EmotionSelector";
import type { CreateFeatureRequestResponse } from "../../types/requests";
import type { MoodCategory } from "../../types/mood";
import { formatMoodCategory } from "../../utils/moodFormatting";
import { getDefaultEmotionForCategory, isValidEmotionForCategory } from "../../utils/moodTaxonomy";

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
    <View style={styles.card}>
      <Text style={styles.title}>Log Emotion + Capture Features</Text>
      <Text style={styles.description}>
        Choose how you feel right now, then submit a feature capture request. The request is queued
        immediately.
      </Text>
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
      <Text style={styles.selectionText}>
        Selected Category:{" "}
        {selectedCategory ? formatMoodCategory(selectedCategory) : "Not selected"}
      </Text>
      <Text style={styles.selectionText}>Selected Emotion: {selectedEmotion ?? "Not selected"}</Text>
      <Pressable
        accessibilityRole="button"
        disabled={isSubmitting || !selectedCategory || !selectedEmotion}
        onPress={handleCreate}
        style={[
          styles.button,
          isSubmitting || !selectedCategory || !selectedEmotion ? styles.buttonDisabled : null
        ]}
        testID="log-emotion-button"
      >
        <Text style={styles.buttonText}>{isSubmitting ? "Logging emotion..." : "Log Emotion"}</Text>
      </Pressable>
      {latestCreated ? (
        <View style={styles.successContainer}>
          <Text style={styles.successTitle}>Emotion logged and request created</Text>
          <Text style={styles.successText}>Request ID: {latestCreated.requestId}</Text>
          <Text style={styles.successText}>Status: {latestCreated.status}</Text>
          <Text style={styles.successText}>
            Mood: {selectedCategory} / {selectedEmotion}
          </Text>
        </View>
      ) : null}
      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
    padding: 16
  },
  title: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "700"
  },
  description: {
    color: "#4b5563",
    fontSize: 14
  },
  selectionText: {
    color: "#4b5563",
    fontSize: 12
  },
  button: {
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  buttonDisabled: {
    opacity: 0.65
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center"
  },
  successContainer: {
    backgroundColor: "#ecfdf5",
    borderColor: "#86efac",
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
    padding: 10
  },
  successTitle: {
    color: "#065f46",
    fontSize: 14,
    fontWeight: "700"
  },
  successText: {
    color: "#065f46",
    fontSize: 13
  },
  errorText: {
    color: "#991b1b",
    fontSize: 14,
    fontWeight: "600"
  }
});
