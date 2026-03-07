import type { MoodCategory, MoodDisplayState, MoodLabelValue } from "../types/mood";

const MOOD_CATEGORY_LABELS: Record<MoodCategory, string> = {
  energized: "Energized",
  calm: "Calm",
  stressed: "Stressed",
  tired: "Tired"
};

function normalizeString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function isMoodCategory(value: string): value is MoodCategory {
  return value === "energized" || value === "calm" || value === "stressed" || value === "tired";
}

export function formatMoodCategory(category: string | null | undefined): string {
  const normalizedCategory = normalizeString(category)?.toLowerCase();
  if (!normalizedCategory || !isMoodCategory(normalizedCategory)) {
    return "Unknown";
  }

  return MOOD_CATEGORY_LABELS[normalizedCategory];
}

export function formatEmotionLabel(emotion: string | null | undefined): string | null {
  return normalizeString(emotion);
}

export function getMoodDisplayModel(label: MoodLabelValue): {
  state: MoodDisplayState;
  categoryLabel: string;
  emotion: string | null;
  text: string;
} {
  if (label === undefined || label === null) {
    return {
      state: "unlabeled",
      categoryLabel: "Unknown",
      emotion: null,
      text: "Not labeled"
    };
  }

  const categoryLabel = formatMoodCategory(label.category);
  const emotion = formatEmotionLabel(label.emotion);

  if (categoryLabel === "Unknown" || !emotion) {
    return {
      state: "unknown",
      categoryLabel: "Unknown",
      emotion: null,
      text: "Unknown"
    };
  }

  return {
    state: "labeled",
    categoryLabel,
    emotion,
    text: `${categoryLabel} — ${emotion}`
  };
}
