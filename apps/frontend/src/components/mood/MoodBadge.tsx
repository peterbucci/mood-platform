import { StyleSheet, Text, View } from "react-native";

import { formatMoodCategory } from "../../utils/moodFormatting";

type MoodBadgeProps = {
  category: string | null | undefined;
};

function getTone(category: string): "energized" | "calm" | "stressed" | "tired" | "unknown" {
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
  return "unknown";
}

export default function MoodBadge({ category }: MoodBadgeProps) {
  const tone = getTone(category ?? "");
  const label = formatMoodCategory(category);

  return (
    <View
      style={[
        styles.badge,
        tone === "energized" ? styles.energized : null,
        tone === "calm" ? styles.calm : null,
        tone === "stressed" ? styles.stressed : null,
        tone === "tired" ? styles.tired : null,
        tone === "unknown" ? styles.unknown : null
      ]}
    >
      <Text
        style={[
          styles.text,
          tone === "energized" ? styles.energizedText : null,
          tone === "calm" ? styles.calmText : null,
          tone === "stressed" ? styles.stressedText : null,
          tone === "tired" ? styles.tiredText : null,
          tone === "unknown" ? styles.unknownText : null
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4
  },
  text: {
    fontSize: 12,
    fontWeight: "700"
  },
  energized: {
    backgroundColor: "#fef3c7",
    borderColor: "#f59e0b"
  },
  calm: {
    backgroundColor: "#dcfce7",
    borderColor: "#22c55e"
  },
  stressed: {
    backgroundColor: "#fee2e2",
    borderColor: "#ef4444"
  },
  tired: {
    backgroundColor: "#ede9fe",
    borderColor: "#8b5cf6"
  },
  unknown: {
    backgroundColor: "#f3f4f6",
    borderColor: "#d1d5db"
  },
  energizedText: {
    color: "#92400e"
  },
  calmText: {
    color: "#166534"
  },
  stressedText: {
    color: "#991b1b"
  },
  tiredText: {
    color: "#5b21b6"
  },
  unknownText: {
    color: "#374151"
  }
});
