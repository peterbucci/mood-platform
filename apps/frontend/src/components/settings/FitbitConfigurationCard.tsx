import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";
import AppButton from "../ui/AppButton";
import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

export type FitbitConfigurationFormValues = {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  scope: string;
  subscriberId: string;
  webhookSecret: string;
};

export type FitbitConfigurationField = keyof FitbitConfigurationFormValues;
export type FitbitConfigurationFieldErrors = Partial<Record<FitbitConfigurationField, string>>;

type FitbitConfigurationCardProps = {
  clientSecretHint?: string | null;
  fieldErrors?: FitbitConfigurationFieldErrors;
  formValues: FitbitConfigurationFormValues;
  isLoading?: boolean;
  isSaving?: boolean;
  loadErrorMessage?: string | null;
  onChangeField: (field: FitbitConfigurationField, value: string) => void;
  onFocusSecretField: (field: "clientSecret" | "webhookSecret") => void;
  onSave: () => void;
  saveErrorMessage?: string | null;
  successMessage?: string | null;
  webhookSecretHint?: string | null;
};

type FormFieldProps = {
  errorMessage?: string | null;
  helperText?: string | null;
  label: string;
  onChangeText: (value: string) => void;
  onFocus?: () => void;
  placeholder?: string;
  value: string;
};

function FormField({
  errorMessage = null,
  helperText = null,
  label,
  onChangeText,
  onFocus,
  placeholder,
  value
}: FormFieldProps) {
  return (
    <View style={styles.fieldBlock}>
      <Text style={styles.fieldLabel}>{label}</Text>
      {helperText ? <InfoText tone="muted">{helperText}</InfoText> : null}
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        onChangeText={onChangeText}
        onFocus={onFocus}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        style={[styles.input, errorMessage ? styles.inputError : null]}
        value={value}
      />
      {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
    </View>
  );
}

export default function FitbitConfigurationCard({
  clientSecretHint = null,
  fieldErrors = {},
  formValues,
  isLoading = false,
  isSaving = false,
  loadErrorMessage = null,
  onChangeField,
  onFocusSecretField,
  onSave,
  saveErrorMessage = null,
  successMessage = null,
  webhookSecretHint = null
}: FitbitConfigurationCardProps) {
  if (isLoading) {
    return (
      <AppCard style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>OAuth Configuration</Text>
          <InfoText tone="helper">Loading your saved Fitbit settings...</InfoText>
        </View>
      </AppCard>
    );
  }

  return (
    <AppCard style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>OAuth Configuration</Text>
        <InfoText tone="helper">
          Save the credentials and webhook details used by the Fitbit connection flow.
        </InfoText>
      </View>

      {loadErrorMessage ? (
        <View style={styles.messageBlock}>
          <Text style={styles.messageTitle}>Unable to load saved configuration</Text>
          <InfoText tone="danger">{loadErrorMessage}</InfoText>
        </View>
      ) : null}

      {successMessage ? (
        <View style={styles.successBlock}>
          <Text style={styles.successTitle}>Configuration saved</Text>
          <InfoText tone="success">{successMessage}</InfoText>
        </View>
      ) : null}

      {saveErrorMessage ? (
        <View style={styles.messageBlock}>
          <Text style={styles.messageTitle}>Unable to save configuration</Text>
          <InfoText tone="danger">{saveErrorMessage}</InfoText>
        </View>
      ) : null}

      <FormField
        errorMessage={fieldErrors.clientId}
        label="Fitbit Client ID"
        onChangeText={(value) => onChangeField("clientId", value)}
        value={formValues.clientId}
      />
      <FormField
        errorMessage={fieldErrors.clientSecret}
        helperText={
          clientSecretHint
            ? `Saved value: ${clientSecretHint}. Edit this field to replace it.`
            : "Required for OAuth token exchange."
        }
        label="Fitbit Client Secret"
        onChangeText={(value) => onChangeField("clientSecret", value)}
        onFocus={() => onFocusSecretField("clientSecret")}
        value={formValues.clientSecret}
      />
      <FormField
        errorMessage={fieldErrors.redirectUri}
        label="Fitbit Redirect URI"
        onChangeText={(value) => onChangeField("redirectUri", value)}
        value={formValues.redirectUri}
      />
      <FormField
        label="Fitbit OAuth Scope"
        onChangeText={(value) => onChangeField("scope", value)}
        value={formValues.scope}
      />
      <FormField
        label="Fitbit Subscriber ID"
        onChangeText={(value) => onChangeField("subscriberId", value)}
        value={formValues.subscriberId}
      />
      <FormField
        helperText={
          webhookSecretHint
            ? `Saved value: ${webhookSecretHint}. Edit this field to replace or clear it.`
            : "Used to verify Fitbit webhook signatures."
        }
        label="Fitbit Webhook Secret"
        onChangeText={(value) => onChangeField("webhookSecret", value)}
        onFocus={() => onFocusSecretField("webhookSecret")}
        value={formValues.webhookSecret}
      />

      <AppButton
        isLoading={isSaving}
        label="Save Configuration"
        onPress={onSave}
        style={styles.saveButton}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  errorText: {
    ...typography.helper,
    color: colors.dangerText
  },
  fieldBlock: {
    gap: spacing.xxs
  },
  fieldLabel: {
    ...typography.helper,
    color: colors.textSecondary,
    fontWeight: "700"
  },
  header: {
    gap: spacing.xxs
  },
  input: {
    ...typography.body,
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.textPrimary,
    minHeight: 44,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  inputError: {
    borderColor: colors.dangerBorder
  },
  messageBlock: {
    backgroundColor: colors.dangerSurface,
    borderColor: colors.dangerBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  messageTitle: {
    ...typography.bodyStrong,
    color: colors.dangerText
  },
  saveButton: {
    alignSelf: "flex-start",
    minWidth: 172
  },
  successBlock: {
    backgroundColor: colors.successSurface,
    borderColor: colors.successBorder,
    borderRadius: radius.sm,
    borderWidth: 1,
    gap: spacing.xxs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  successTitle: {
    ...typography.bodyStrong,
    color: colors.successText
  },
  title: {
    ...typography.sectionTitle,
    color: colors.textPrimary
  }
});
