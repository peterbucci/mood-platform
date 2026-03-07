export type MoodCategory = "energized" | "calm" | "stressed" | "tired";

export type MoodLabel = {
  category: MoodCategory;
  emotion: string;
};

export type MoodLabelValue =
  | {
      category?: string | null;
      emotion?: string | null;
    }
  | null
  | undefined;

export type MoodDisplayState = "labeled" | "unlabeled" | "unknown";
