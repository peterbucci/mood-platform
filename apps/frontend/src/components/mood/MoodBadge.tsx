import { formatMoodCategory } from "../../utils/moodFormatting";
import AppStatusBadge from "../ui/StatusBadge";

type MoodBadgeProps = {
  category: string | null | undefined;
};

function getTone(category: string): "energized" | "calm" | "stressed" | "tired" | "neutral" {
  const normalized = category.toLowerCase();
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

export default function MoodBadge({ category }: MoodBadgeProps) {
  const tone = getTone(category ?? "");
  const label = formatMoodCategory(category);

  return <AppStatusBadge label={label} tone={tone} />;
}
