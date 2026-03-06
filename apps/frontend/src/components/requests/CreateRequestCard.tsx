import { useCallback, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { createFeatureRequest } from "../../api/requests";
import type { CreateFeatureRequestResponse } from "../../types/requests";

type CreateRequestCardProps = {
  onCreated?: (request: CreateFeatureRequestResponse) => Promise<void> | void;
};

const DEFAULT_ERROR_MESSAGE = "Unable to create request right now.";

export default function CreateRequestCard({ onCreated }: CreateRequestCardProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latestCreated, setLatestCreated] = useState<CreateFeatureRequestResponse | null>(null);
  const inFlightRef = useRef(false);

  const handleCreate = useCallback(async () => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const created = await createFeatureRequest();
      setLatestCreated(created);
      if (onCreated) {
        await onCreated(created);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : DEFAULT_ERROR_MESSAGE;
      setErrorMessage(message);
    } finally {
      inFlightRef.current = false;
      setIsSubmitting(false);
    }
  }, [onCreated]);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Capture Latest Features</Text>
      <Text style={styles.description}>
        Submit a new feature capture request. It will enter the pending queue immediately.
      </Text>
      <Pressable
        accessibilityRole="button"
        disabled={isSubmitting}
        onPress={handleCreate}
        style={[styles.button, isSubmitting ? styles.buttonDisabled : null]}
      >
        <Text style={styles.buttonText}>
          {isSubmitting ? "Creating request..." : "Request Feature Capture"}
        </Text>
      </Pressable>
      {latestCreated ? (
        <View style={styles.successContainer}>
          <Text style={styles.successTitle}>Request created</Text>
          <Text style={styles.successText}>Request ID: {latestCreated.requestId}</Text>
          <Text style={styles.successText}>Status: {latestCreated.status}</Text>
        </View>
      ) : null}
      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
    padding: 16
  },
  title: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "700"
  },
  description: {
    color: "#4b5563",
    fontSize: 14
  },
  button: {
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  buttonDisabled: {
    opacity: 0.65
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center"
  },
  successContainer: {
    backgroundColor: "#ecfdf5",
    borderColor: "#86efac",
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
    padding: 10
  },
  successTitle: {
    color: "#065f46",
    fontSize: 14,
    fontWeight: "700"
  },
  successText: {
    color: "#065f46",
    fontSize: 13
  },
  errorText: {
    color: "#991b1b",
    fontSize: 14,
    fontWeight: "600"
  }
});
