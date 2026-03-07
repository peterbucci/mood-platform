import type { MoodCategory } from "../../types/mood";
import { MOOD_TAXONOMY } from "../../utils/moodTaxonomy";

export type DashboardCategoryTheme = {
  accentSurface: string;
  bar: string;
  border: string;
  fill: string;
  line: string;
  softSurface: string;
  text: string;
};

const CATEGORY_THEMES: Record<MoodCategory, DashboardCategoryTheme> = {
  calm: {
    accentSurface: "#e0efe5",
    bar: "#789f84",
    border: "#bfd4c6",
    fill: "#93b8a0",
    line: "#6f977c",
    softSurface: "#f2f8f3",
    text: "#2b5338"
  },
  energized: {
    accentSurface: "#dfeafe",
    bar: "#678fc8",
    border: "#bfd1ef",
    fill: "#86abdf",
    line: "#5f86c0",
    softSurface: "#f1f6fd",
    text: "#244371"
  },
  stressed: {
    accentSurface: "#fee6da",
    bar: "#d1835e",
    border: "#f0c9b4",
    fill: "#e2a07f",
    line: "#c97a54",
    softSurface: "#fff5ef",
    text: "#8f4424"
  },
  tired: {
    accentSurface: "#ece5fb",
    bar: "#9b88c6",
    border: "#d9cef1",
    fill: "#b09fd6",
    line: "#927fbe",
    softSurface: "#f7f4fd",
    text: "#5b4d7d"
  }
};

const EMOTION_VARIANTS: Record<MoodCategory, readonly string[]> = {
  calm: ["#5f8f71", "#6fa07f", "#81af8e", "#94bc9d"],
  energized: ["#5278bb", "#6389c8", "#769ad4", "#89addf"],
  stressed: ["#c86e47", "#d47f5b", "#de9070", "#e7a387"],
  tired: ["#886fbc", "#967fc6", "#a58fd0", "#b6a2db"]
};

export function getDashboardCategoryTheme(category: MoodCategory): DashboardCategoryTheme {
  return CATEGORY_THEMES[category];
}

export function getDashboardEmotionColor(category: MoodCategory, emotion: string): string {
  const emotionIndex = MOOD_TAXONOMY[category].findIndex(
    (candidate) => candidate.toLowerCase() === emotion.toLowerCase()
  );

  if (emotionIndex < 0) {
    return CATEGORY_THEMES[category].line;
  }

  return EMOTION_VARIANTS[category][emotionIndex] ?? CATEGORY_THEMES[category].line;
}
