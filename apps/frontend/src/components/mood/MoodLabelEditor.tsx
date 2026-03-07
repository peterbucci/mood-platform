import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { MoodCategory, MoodLabelValue } from "../../types/mood";
import { formatMoodCategory } from "../../utils/moodFormatting";
import {
  getDefaultEmotionForCategory,
  isMoodCategory,
  isValidEmotionForCategory
} from "../../utils/moodTaxonomy";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import CategorySelector from "./CategorySelector";
import EmotionSelector from "./EmotionSelector";

type MoodLabelEditorProps = {
  initialLabel: MoodLabelValue;
  onSaveLabel: (category: MoodCategory, emotion: string) => Promise<void>;
};

type EditableMoodSelection = {
  category: MoodCategory | null;
  emotion: string | null;
};

function normalizeString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function getInitialSelection(label: MoodLabelValue): EditableMoodSelection {
  if (!label) {
    return {
      category: null,
      emotion: null
    };
  }

  const normalizedCategory = normalizeString(label.category)?.toLowerCase();
  const normalizedEmotion = normalizeString(label.emotion);

  if (!normalizedCategory || !isMoodCategory(normalizedCategory)) {
    return {
      category: null,
      emotion: null
    };
  }

  if (normalizedEmotion && isValidEmotionForCategory(normalizedCategory, normalizedEmotion)) {
    return {
      category: normalizedCategory,
      emotion: normalizedEmotion
    };
  }

  return {
    category: normalizedCategory,
    emotion: null
  };
}

export default function MoodLabelEditor({ initialLabel, onSaveLabel }: MoodLabelEditorProps) {
  const [selectedCategory, setSelectedCategory] = useState<MoodCategory | null>(null);
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  const isInitiallyLabeled = useMemo(() => {
    const initial = getInitialSelection(initialLabel);
    return Boolean(initial.category && initial.emotion);
  }, [initialLabel]);

  useEffect(() => {
    const initial = getInitialSelection(initialLabel);
    setSelectedCategory(initial.category);
    setSelectedEmotion(initial.emotion);
    setErrorMessage(null);
    setSuccessMessage(null);
  }, [initialLabel]);

  const handleSelectCategory = useCallback(
    (category: MoodCategory) => {
      setSelectedCategory(category);
      setSelectedEmotion((current) => {
        if (current && isValidEmotionForCategory(category, current)) {
          return current;
        }
        return getDefaultEmotionForCategory(category);
      });
      setErrorMessage(null);
      setSuccessMessage(null);
    },
    []
  );

  const handleSelectEmotion = useCallback((emotion: string) => {
    setSelectedEmotion(emotion);
    setErrorMessage(null);
    setSuccessMessage(null);
  }, []);

  const handleSave = useCallback(async () => {
    if (inFlightRef.current || !selectedCategory || !selectedEmotion) {
      if (!selectedCategory || !selectedEmotion) {
        setErrorMessage("Please select both category and emotion.");
      }
      return;
    }

    inFlightRef.current = true;
    setIsSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await onSaveLabel(selectedCategory, selectedEmotion);
      setSuccessMessage("Mood label saved.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save mood label.";
      setErrorMessage(message);
    } finally {
      inFlightRef.current = false;
      setIsSaving(false);
    }
  }, [onSaveLabel, selectedCategory, selectedEmotion]);

  return (
    <AppCard style={styles.card}>
      <Text style={styles.title}>{isInitiallyLabeled ? "Update Mood Label" : "Add Mood Label"}</Text>
      <CategorySelector
        disabled={isSaving}
        onSelectCategory={handleSelectCategory}
        selectedCategory={selectedCategory}
      />
      <EmotionSelector
        category={selectedCategory}
        disabled={isSaving || !selectedCategory}
        onSelectEmotion={handleSelectEmotion}
        selectedEmotion={selectedEmotion}
      />
      <Text style={styles.selectionText} testID="mood-editor-category-value">
        Selected Category: {selectedCategory ? formatMoodCategory(selectedCategory) : "Not selected"}
      </Text>
      <Text style={styles.selectionText} testID="mood-editor-emotion-value">
        Selected Emotion: {selectedEmotion ?? "Not selected"}
      </Text>

      <AppButton
        disabled={isSaving || !selectedCategory || !selectedEmotion}
        isLoading={isSaving}
        label="Save Label"
        onPress={handleSave}
        style={styles.saveButton}
        testID="mood-save-button"
      />

      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      {successMessage ? <Text style={styles.successText}>{successMessage}</Text> : null}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.sm
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  selectionText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  saveButton: {
    alignSelf: "flex-start"
  },
  errorText: {
    ...typography.bodyStrong,
    color: colors.dangerText
  },
  successText: {
    ...typography.bodyStrong,
    color: colors.successText
  }
});
