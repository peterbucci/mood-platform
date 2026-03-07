import { StyleSheet, View } from "react-native";

import { spacing } from "../../theme";
import AppButton from "../ui/AppButton";
import InfoText from "../ui/InfoText";

type BusyAction = "connect" | "disconnect" | null;

type FitbitActionButtonsProps = {
  busyAction?: BusyAction;
  connected: boolean;
  isRefreshing?: boolean;
  onConnect: () => void;
  onDisconnect?: () => void;
  onRefresh?: () => void;
};

export default function FitbitActionButtons({
  busyAction = null,
  connected,
  isRefreshing = false,
  onConnect,
  onDisconnect,
  onRefresh
}: FitbitActionButtonsProps) {
  return (
    <View style={styles.container}>
      <View style={styles.safeActionRow}>
        <AppButton
          isLoading={busyAction === "connect"}
          label={connected ? "Reconnect Fitbit" : "Connect Fitbit"}
          onPress={onConnect}
          style={styles.safeActionButton}
        />
        {connected && onRefresh ? (
          <AppButton
            disabled={busyAction !== null}
            isLoading={isRefreshing}
            label="Refresh Connection"
            onPress={onRefresh}
            style={styles.safeActionButton}
            variant="outline"
          />
        ) : null}
      </View>

      {connected && onDisconnect ? (
        <View style={styles.disconnectSection}>
          <InfoText tone="muted">Disconnecting will stop new feature captures from Fitbit.</InfoText>
          <AppButton
            isLoading={busyAction === "disconnect"}
            label="Disconnect Fitbit"
            onPress={onDisconnect}
            style={styles.disconnectButton}
            variant="danger"
          />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md
  },
  disconnectButton: {
    minWidth: 168
  },
  disconnectSection: {
    borderTopWidth: 0,
    gap: spacing.sm,
    paddingTop: spacing.xs
  },
  safeActionButton: {
    flexGrow: 1,
    minWidth: 148
  },
  safeActionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  }
});
