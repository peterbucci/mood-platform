import { StyleSheet, Text, View } from "react-native";

type ErrorStateProps = {
  message: string;
};

export default function ErrorState({ message }: ErrorStateProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Something went wrong</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fef2f2",
    borderColor: "#fecaca",
    borderRadius: 12,
    borderWidth: 1,
    gap: 6,
    padding: 16
  },
  title: {
    color: "#991b1b",
    fontSize: 15,
    fontWeight: "700"
  },
  message: {
    color: "#7f1d1d",
    fontSize: 14
  }
});
