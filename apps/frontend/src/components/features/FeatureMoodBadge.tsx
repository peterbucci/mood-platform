import StatusBadge from "../ui/StatusBadge";
import { formatMoodCategory } from "../../utils/moodFormatting";

type FeatureMoodBadgeProps = {
  category: string | null | undefined;
  fallbackLabel?: string;
};

function getTone(category: string | null | undefined): "energized" | "calm" | "stressed" | "tired" | "neutral" {
  const normalized = category?.toLowerCase();
  if (normalized === "energized") {
    return "energized";
  }
  if (normalized === "calm") {
    return "calm";
  }
  if (normalized === "stressed") {
    return "stressed";
  }
  if (normalized === "tired") {
    return "tired";
  }

  return "neutral";
}

export default function FeatureMoodBadge({ category, fallbackLabel = "Not labeled" }: FeatureMoodBadgeProps) {
  const tone = getTone(category);
  const label = tone === "neutral" ? fallbackLabel : formatMoodCategory(category);

  return <StatusBadge label={label} tone={tone} />;
}
