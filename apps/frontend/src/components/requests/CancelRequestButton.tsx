import { Pressable, StyleSheet, Text } from "react-native";

type CancelRequestButtonProps = {
  disabled?: boolean;
  isLoading?: boolean;
  onPress: () => void;
};

export default function CancelRequestButton({
  disabled = false,
  isLoading = false,
  onPress
}: CancelRequestButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || isLoading}
      onPress={onPress}
      style={[
        styles.button,
        disabled || isLoading ? styles.buttonDisabled : null
      ]}
    >
      <Text style={styles.buttonText}>{isLoading ? "Canceling..." : "Cancel Request"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: "flex-start",
    backgroundColor: "#b91c1c",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  buttonDisabled: {
    opacity: 0.65
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700"
  }
});
