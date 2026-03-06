import { StyleSheet, Text, View } from "react-native";

type EmptyStateProps = {
  message: string;
};

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 12,
    borderStyle: "dashed",
    borderWidth: 1,
    padding: 16
  },
  message: {
    color: "#4b5563",
    fontSize: 14
  }
});
