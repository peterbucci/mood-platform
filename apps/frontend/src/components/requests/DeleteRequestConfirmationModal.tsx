import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import type { FeatureRequestRecord } from "../../types/requests";
import { colors, radius, spacing, typography } from "../../theme";
import {
  formatRequestTimestamp,
  shortenRequestId
} from "../../utils/requestFormatting";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type DeleteRequestConfirmationModalProps = {
  errorMessage?: string | null;
  isDeleting?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  request: FeatureRequestRecord | null;
  visible: boolean;
};

export default function DeleteRequestConfirmationModal({
  errorMessage = null,
  isDeleting = false,
  onCancel,
  onConfirm,
  request,
  visible
}: DeleteRequestConfirmationModalProps) {
  if (!visible || !request) {
    return null;
  }

  return (
    <Modal
      animationType="fade"
      onRequestClose={isDeleting ? undefined : onCancel}
      transparent
      visible={visible}
    >
      <View style={styles.overlay}>
        <Pressable
          accessibilityRole="button"
          disabled={isDeleting}
          onPress={onCancel}
          style={StyleSheet.absoluteFill}
          testID="delete-request-modal-overlay"
        />
        <AppCard style={styles.card} testID="delete-request-modal">
          <View style={styles.header}>
            <Text style={styles.title}>Delete Request?</Text>
            <InfoText tone="helper">
              Review what will be removed before confirming this action.
            </InfoText>
          </View>

          <View style={styles.contextBlock}>
            <Text style={styles.contextLabel}>Request</Text>
            <Text style={styles.contextValue}>{`ID ${shortenRequestId(request.id)}`}</Text>
            <InfoText tone="muted">{formatRequestTimestamp(request.createdAt)}</InfoText>
          </View>

          <View style={styles.body}>
            <InfoText>This will permanently delete the request.</InfoText>
            <InfoText>
              {request.featureId
                ? "This request has a linked feature snapshot. It will also be deleted."
                : "If this request has a linked feature snapshot, it will also be deleted."}
            </InfoText>
            <InfoText>Any linked mood labels or related records will also be removed.</InfoText>
            <InfoText tone="danger">This action cannot be undone.</InfoText>
          </View>

          {errorMessage ? (
            <View style={styles.errorBlock}>
              <Text style={styles.errorTitle}>Unable to delete request</Text>
              <InfoText tone="danger">{errorMessage}</InfoText>
            </View>
          ) : null}

          <View style={styles.actions}>
            <AppButton
              disabled={isDeleting}
              label="Cancel"
              onPress={onCancel}
              style={styles.actionButton}
              variant="outline"
            />
            <AppButton
              isLoading={isDeleting}
              label="Delete Request"
              onPress={onConfirm}
              style={styles.actionButton}
              testID="confirm-delete-request-button"
              variant="danger"
            />
          </View>
        </AppCard>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    flex: 1
  },
  actions: {
    flexDirection: "row",
    gap: spacing.sm
  },
  body: {
    gap: spacing.xs
  },
  card: {
    gap: spacing.md,
    marginHorizontal: spacing.lg,
    maxWidth: 420,
    width: "100%"
  },
  contextBlock: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  contextLabel: {
    ...typography.helper,
    color: colors.textMuted,
    textTransform: "uppercase"
  },
  contextValue: {
    ...typography.bodyStrong,
    color: colors.textPrimary
  },
  errorBlock: {
    backgroundColor: colors.dangerSurface,
    borderColor: colors.dangerBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  errorTitle: {
    ...typography.bodyStrong,
    color: colors.dangerText
  },
  header: {
    gap: spacing.xxs
  },
  overlay: {
    alignItems: "center",
    backgroundColor: "rgba(17, 24, 39, 0.36)",
    flex: 1,
    justifyContent: "center",
    padding: spacing.lg
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  }
});
