import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";
import type { MoodCategory, MoodLabelValue } from "../../types/mood";
import {
  getDefaultEmotionForCategory,
  isMoodCategory,
  isValidEmotionForCategory
} from "../../utils/moodTaxonomy";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";
import CategorySelector from "./CategorySelector";
import EmotionSelector from "./EmotionSelector";
import MoodPreviewCard from "./MoodPreviewCard";

type MoodLabelEditorProps = {
  initialLabel: MoodLabelValue;
  onSaveLabel: (category: MoodCategory, emotion: string) => Promise<void>;
  onCancel?: () => void;
  showTitle?: boolean;
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

export default function MoodLabelEditor({
  initialLabel,
  onSaveLabel,
  onCancel,
  showTitle = true
}: MoodLabelEditorProps) {
  const [selectedCategory, setSelectedCategory] = useState<MoodCategory | null>(null);
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  const isInitiallyLabeled = useMemo(() => {
    const initial = getInitialSelection(initialLabel);
    return Boolean(initial.category && initial.emotion);
  }, [initialLabel]);

  const previewLabel = useMemo<MoodLabelValue>(() => {
    if (!selectedCategory || !selectedEmotion) {
      return undefined;
    }

    return {
      category: selectedCategory,
      emotion: selectedEmotion
    };
  }, [selectedCategory, selectedEmotion]);

  useEffect(() => {
    const initial = getInitialSelection(initialLabel);
    setSelectedCategory(initial.category);
    setSelectedEmotion(initial.emotion);
    setErrorMessage(null);
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
    },
    []
  );

  const handleSelectEmotion = useCallback((emotion: string) => {
    setSelectedEmotion(emotion);
    setErrorMessage(null);
  }, []);

  const handleSave = useCallback(async () => {
    if (inFlightRef.current || !selectedCategory || !selectedEmotion) {
      if (!selectedCategory || !selectedEmotion) {
        setErrorMessage("Please select both a category and an emotion.");
      }
      return;
    }

    inFlightRef.current = true;
    setIsSaving(true);
    setErrorMessage(null);

    try {
      await onSaveLabel(selectedCategory, selectedEmotion);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save mood label.";
      setErrorMessage(message);
    } finally {
      inFlightRef.current = false;
      setIsSaving(false);
    }
  }, [onSaveLabel, selectedCategory, selectedEmotion]);

  return (
    <View style={styles.container}>
      <MoodPreviewCard label={previewLabel} />

      <AppCard style={styles.selectionCard}>
        {showTitle ? (
          <View style={styles.header}>
            <Text style={styles.title}>{isInitiallyLabeled ? "Update Mood Label" : "Add Mood Label"}</Text>
            <InfoText tone="helper">Choose a category first, then confirm the emotion that fits best.</InfoText>
          </View>
        ) : (
          <View style={styles.header}>
            <Text style={styles.title}>Mood Selection</Text>
            <InfoText tone="helper">Choose a category first, then confirm the emotion that fits best.</InfoText>
          </View>
        )}

        <View style={styles.selectionGroup}>
          <InfoText tone="helper">Start with the broad mood category.</InfoText>
          <CategorySelector
            disabled={isSaving}
            onSelectCategory={handleSelectCategory}
            selectedCategory={selectedCategory}
          />
        </View>

        <View style={styles.selectionGroup}>
          <InfoText tone="helper">Then pick the emotion that feels most accurate.</InfoText>
          <EmotionSelector
            category={selectedCategory}
            disabled={isSaving || !selectedCategory}
            onSelectEmotion={handleSelectEmotion}
            selectedEmotion={selectedEmotion}
          />
        </View>

        <View style={styles.actions}>
          <AppButton
            disabled={isSaving || !selectedCategory || !selectedEmotion}
            isLoading={isSaving}
            label="Save Label"
            onPress={handleSave}
            style={styles.primaryButton}
            testID="mood-save-button"
          />
          {onCancel ? (
            <AppButton
              disabled={isSaving}
              label="Cancel"
              onPress={onCancel}
              style={styles.secondaryButton}
              variant="outline"
            />
          ) : null}
        </View>

        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      </AppCard>
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: "row",
    gap: spacing.sm
  },
  container: {
    gap: spacing.md
  },
  errorText: {
    ...typography.bodyStrong,
    color: colors.dangerText
  },
  header: {
    gap: spacing.xxs
  },
  primaryButton: {
    flex: 1
  },
  secondaryButton: {
    minWidth: 110
  },
  selectionCard: {
    gap: spacing.md
  },
  selectionGroup: {
    gap: spacing.xs
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  }
});
