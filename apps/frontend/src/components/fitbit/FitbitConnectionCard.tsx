import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FitbitConnectionStatus } from "../../types/fitbit";

type FitbitConnectionCardProps = {
  status: FitbitConnectionStatus;
  isBusy?: boolean;
  onConnect: () => void;
  onDisconnect?: () => void;
  onRefresh: () => void;
};

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "N/A";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export default function FitbitConnectionCard({
  status,
  isBusy = false,
  onConnect,
  onDisconnect,
  onRefresh
}: FitbitConnectionCardProps) {
  if (!status.connected) {
    return (
      <View style={[styles.card, styles.disconnectedCard]}>
        <Text style={styles.title}>Fitbit not connected</Text>
        <Text style={styles.description}>
          Feature requests may not be fulfilled until your Fitbit account is connected.
        </Text>
        <Pressable
          accessibilityRole="button"
          disabled={isBusy}
          onPress={onConnect}
          style={[styles.primaryButton, isBusy ? styles.buttonDisabled : null]}
        >
          <Text style={styles.primaryButtonText}>
            {isBusy ? "Opening Fitbit..." : "Connect Fitbit"}
          </Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={[styles.card, styles.connectedCard]}>
      <Text style={styles.title}>Fitbit connected</Text>
      <Text style={styles.description}>Your account is ready for feature fulfillment.</Text>
      <View style={styles.metaContainer}>
        <Text style={styles.metaRow}>Status: Connected</Text>
        <Text style={styles.metaRow}>Fitbit user id: {status.fitbitUserId ?? "N/A"}</Text>
        <Text style={styles.metaRow}>Last sync: {formatDate(status.lastSyncAt)}</Text>
        <Text style={styles.metaRow}>Expires: {formatDate(status.expiresAt)}</Text>
        <Text style={styles.metaRow}>
          Scopes: {status.scopes && status.scopes.length > 0 ? status.scopes.join(", ") : "N/A"}
        </Text>
      </View>
      <View style={styles.actionRow}>
        <Pressable
          accessibilityRole="button"
          disabled={isBusy}
          onPress={onRefresh}
          style={[styles.secondaryButton, isBusy ? styles.buttonDisabled : null]}
        >
          <Text style={styles.secondaryButtonText}>Refresh Status</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          disabled={isBusy}
          onPress={onConnect}
          style={[styles.secondaryButton, isBusy ? styles.buttonDisabled : null]}
        >
          <Text style={styles.secondaryButtonText}>Reconnect Fitbit</Text>
        </Pressable>
        {onDisconnect ? (
          <Pressable
            accessibilityRole="button"
            disabled={isBusy}
            onPress={onDisconnect}
            style={[styles.dangerButton, isBusy ? styles.buttonDisabled : null]}
          >
            <Text style={styles.dangerButtonText}>Disconnect Fitbit</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
    padding: 16
  },
  disconnectedCard: {
    backgroundColor: "#fff7ed",
    borderColor: "#fed7aa"
  },
  connectedCard: {
    backgroundColor: "#ecfdf5",
    borderColor: "#86efac"
  },
  title: {
    color: "#111827",
    fontSize: 20,
    fontWeight: "700"
  },
  description: {
    color: "#374151",
    fontSize: 15
  },
  metaContainer: {
    backgroundColor: "#ffffff",
    borderColor: "#d1fae5",
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
    padding: 10
  },
  metaRow: {
    color: "#1f2937",
    fontSize: 13
  },
  actionRow: {
    flexDirection: "column",
    gap: 8
  },
  primaryButton: {
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center"
  },
  secondaryButton: {
    backgroundColor: "#111827",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  secondaryButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600",
    textAlign: "center"
  },
  dangerButton: {
    backgroundColor: "#b91c1c",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  dangerButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600",
    textAlign: "center"
  },
  buttonDisabled: {
    opacity: 0.65
  }
});
