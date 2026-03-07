import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { MoodCategory, MoodLabelValue } from "../../types/mood";
import { formatMoodCategory } from "../../utils/moodFormatting";
import {
  getDefaultEmotionForCategory,
  isMoodCategory,
  isValidEmotionForCategory
} from "../../utils/moodTaxonomy";
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
    <View style={styles.card}>
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

      <Pressable
        accessibilityRole="button"
        disabled={isSaving || !selectedCategory || !selectedEmotion}
        onPress={handleSave}
        style={[styles.saveButton, isSaving || !selectedCategory || !selectedEmotion ? styles.saveButtonDisabled : null]}
        testID="mood-save-button"
      >
        <Text style={styles.saveButtonText}>{isSaving ? "Saving..." : "Save Label"}</Text>
      </Pressable>

      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
      {successMessage ? <Text style={styles.successText}>{successMessage}</Text> : null}
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
    padding: 14
  },
  title: {
    color: "#111827",
    fontSize: 16,
    fontWeight: "700"
  },
  selectionText: {
    color: "#4b5563",
    fontSize: 12
  },
  saveButton: {
    alignSelf: "flex-start",
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  saveButtonDisabled: {
    opacity: 0.6
  },
  saveButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600"
  },
  errorText: {
    color: "#b91c1c",
    fontSize: 13,
    fontWeight: "600"
  },
  successText: {
    color: "#166534",
    fontSize: 13,
    fontWeight: "600"
  }
});
