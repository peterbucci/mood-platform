import { Modal, Pressable, StyleSheet, Text, View } from "react-native";

import type { FeatureRecord } from "../../types/features";
import { colors, radius, spacing, typography } from "../../theme";
import {
  formatFeatureTimestamp,
  shortenFeatureId
} from "../../utils/featureHistoryFormatting";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type DeleteFeatureConfirmationModalProps = {
  errorMessage?: string | null;
  feature: FeatureRecord | null;
  isDeleting?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  visible: boolean;
};

export default function DeleteFeatureConfirmationModal({
  errorMessage = null,
  feature,
  isDeleting = false,
  onCancel,
  onConfirm,
  visible
}: DeleteFeatureConfirmationModalProps) {
  if (!visible || !feature) {
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
          testID="delete-feature-modal-overlay"
        />
        <AppCard style={styles.card} testID="delete-feature-modal">
          <View style={styles.header}>
            <Text style={styles.title}>Delete Feature Snapshot?</Text>
            <InfoText tone="helper">
              Review what will be removed before confirming this action.
            </InfoText>
          </View>

          <View style={styles.contextBlock}>
            <Text style={styles.contextLabel}>Feature Snapshot</Text>
            <Text style={styles.contextValue}>{`ID ${shortenFeatureId(feature.id)}`}</Text>
            <InfoText tone="muted">{formatFeatureTimestamp(feature.createdAt)}</InfoText>
          </View>

          <View style={styles.body}>
            <InfoText>This will permanently delete the feature snapshot.</InfoText>
            <InfoText>Any linked mood labels will also be removed.</InfoText>
            <InfoText>
              If a request is linked to this snapshot, it may also be deleted according to the platform&apos;s
              data cleanup policy.
            </InfoText>
            <InfoText tone="danger">This action cannot be undone.</InfoText>
          </View>

          {errorMessage ? (
            <View style={styles.errorBlock}>
              <Text style={styles.errorTitle}>Unable to delete feature snapshot</Text>
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
              label="Delete Snapshot"
              onPress={onConfirm}
              style={styles.actionButton}
              testID="confirm-delete-feature-button"
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
