import { StyleSheet, Text, View } from "react-native";

type FeatureValueRowProps = {
  label: string;
  value: string;
};

export default function FeatureValueRow({ label, value }: FeatureValueRowProps) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8,
    justifyContent: "space-between"
  },
  label: {
    color: "#374151",
    flex: 1,
    fontSize: 13
  },
  value: {
    color: "#111827",
    flex: 1,
    fontSize: 13,
    fontWeight: "700",
    textAlign: "right"
  }
});
