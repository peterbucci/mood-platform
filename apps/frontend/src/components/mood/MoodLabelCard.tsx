import { StyleSheet, Text, View } from "react-native";

import type { MoodLabelValue } from "../../types/mood";
import { getMoodDisplayModel } from "../../utils/moodFormatting";
import MoodBadge from "./MoodBadge";

type MoodLabelCardProps = {
  label: MoodLabelValue;
};

export default function MoodLabelCard({ label }: MoodLabelCardProps) {
  const mood = getMoodDisplayModel(label);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Mood</Text>
      {mood.state === "labeled" && mood.emotion ? (
        <View style={styles.labeledRow}>
          <MoodBadge category={label?.category} />
          <Text style={styles.labeledText}>— {mood.emotion}</Text>
        </View>
      ) : (
        <Text style={styles.fallbackText}>{mood.text}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
    padding: 14
  },
  title: {
    color: "#111827",
    fontSize: 16,
    fontWeight: "700"
  },
  labeledRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8
  },
  labeledText: {
    color: "#111827",
    fontSize: 14,
    fontWeight: "600"
  },
  fallbackText: {
    color: "#4b5563",
    fontSize: 14,
    fontWeight: "600"
  }
});
