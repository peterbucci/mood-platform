import type { ReactNode } from "react";
import { StyleSheet, Text } from "react-native";

import { colors, typography } from "../../theme";

type InfoTextTone = "default" | "muted" | "helper" | "success" | "warning" | "danger";

type InfoTextProps = {
  children: ReactNode;
  tone?: InfoTextTone;
};

function toneColor(tone: InfoTextTone): string {
  if (tone === "muted") {
    return colors.textMuted;
  }
  if (tone === "helper") {
    return colors.textSecondary;
  }
  if (tone === "success") {
    return colors.successText;
  }
  if (tone === "warning") {
    return colors.warningText;
  }
  if (tone === "danger") {
    return colors.dangerText;
  }
  return colors.textPrimary;
}

export default function InfoText({ children, tone = "default" }: InfoTextProps) {
  return (
    <Text style={[styles.text, tone === "helper" ? styles.helperText : null, { color: toneColor(tone) }]}>
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: {
    ...typography.body
  },
  helperText: {
    ...typography.helper
  }
});
