import type { MoodCategory } from "../types/mood";

export const MOOD_TAXONOMY: Record<MoodCategory, readonly string[]> = {
  energized: ["Happy", "Excited", "Motivated", "Cheerful"],
  calm: ["Calm", "Relaxed", "Content", "Peaceful"],
  stressed: ["Stressed", "Anxious", "Overwhelmed", "Nervous"],
  tired: ["Tired", "Sad", "Low", "Drained"]
};

export const MOOD_CATEGORIES: readonly MoodCategory[] = [
  "energized",
  "calm",
  "stressed",
  "tired"
];

export function isMoodCategory(value: string): value is MoodCategory {
  return MOOD_CATEGORIES.includes(value as MoodCategory);
}

export function getEmotionOptionsForCategory(
  category: MoodCategory | null | undefined
): readonly string[] {
  if (!category) {
    return [];
  }

  return MOOD_TAXONOMY[category];
}

export function isValidEmotionForCategory(
  category: MoodCategory | null | undefined,
  emotion: string | null | undefined
): boolean {
  if (!category || !emotion) {
    return false;
  }

  return MOOD_TAXONOMY[category].includes(emotion);
}

export function getDefaultEmotionForCategory(category: MoodCategory): string {
  return MOOD_TAXONOMY[category][0];
}
