import { StyleSheet, Text, View } from "react-native";

import type { MoodCategory } from "../../types/mood";
import { formatMoodCategory } from "../../utils/moodFormatting";
import { colors, radius, spacing, typography } from "../../theme";
import AppCard from "../ui/AppCard";
import { getDashboardCategoryTheme } from "./dashboardTheme";

type MoodSummaryCardProps = {
  category: MoodCategory | null;
  emotion: string | null;
  entriesToday: number;
  isToday: boolean;
  lastLogged: string;
  message: string;
};

export default function MoodSummaryCard({
  category,
  emotion,
  entriesToday,
  isToday,
  lastLogged,
  message
}: MoodSummaryCardProps) {
  const theme = category ? getDashboardCategoryTheme(category) : null;
  const entriesLabel = `${entriesToday} ${entriesToday === 1 ? "entry" : "entries"} today`;

  if (!category || !emotion || !theme) {
    return (
      <AppCard style={styles.card}>
        <View style={styles.headerRow}>
          <View style={styles.titleBlock}>
            <Text style={styles.title}>Today's Mood</Text>
            <Text style={styles.subtitle}>Your daily snapshot will appear here once you log a mood.</Text>
          </View>
          <View style={styles.countPill}>
            <Text style={styles.countText}>{entriesLabel}</Text>
          </View>
        </View>
        <View style={styles.emptyState}>
          <View style={styles.emptyGlyph}>
            <Text style={styles.emptyGlyphText}>--</Text>
          </View>
          <View style={styles.emptyCopy}>
            <Text style={styles.emptyTitle}>No mood logged yet</Text>
            <Text style={styles.emptySubtitle}>{message}</Text>
          </View>
        </View>
      </AppCard>
    );
  }

  return (
    <AppCard style={[styles.card, { borderColor: theme.border }]}>
      <View style={styles.headerRow}>
        <View style={styles.titleBlock}>
          <Text style={styles.title}>Today's Mood</Text>
          <Text style={styles.subtitle}>{message}</Text>
        </View>
        <View style={[styles.countPill, { backgroundColor: theme.softSurface, borderColor: theme.border }]}>
          <Text style={[styles.countText, { color: theme.text }]}>{entriesLabel}</Text>
        </View>
      </View>

      <View style={styles.snapshotRow}>
        <View style={styles.snapshotCopy}>
          <Text style={styles.emotion}>{emotion}</Text>
          <View style={styles.metaRow}>
            <View style={[styles.categoryPill, { backgroundColor: theme.accentSurface, borderColor: theme.border }]}>
              <View style={[styles.categoryDot, { backgroundColor: theme.line }]} />
              <Text style={[styles.categoryText, { color: theme.text }]}>{formatMoodCategory(category)}</Text>
            </View>
            <Text style={styles.lastLogged}>
              Last logged {lastLogged}
              {!isToday ? " | latest entry" : ""}
            </Text>
          </View>
        </View>

        <View style={[styles.emotionGlyph, { backgroundColor: theme.softSurface, borderColor: theme.border }]}>
          <Text style={[styles.emotionGlyphText, { color: theme.line }]}>{emotion.slice(0, 1).toUpperCase()}</Text>
        </View>
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md
  },
  categoryDot: {
    borderRadius: radius.pill,
    height: 8,
    width: 8
  },
  categoryPill: {
    alignItems: "center",
    borderRadius: radius.pill,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  categoryText: {
    ...typography.bodyStrong
  },
  countPill: {
    alignSelf: "flex-start",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  countText: {
    ...typography.helper,
    color: colors.textSecondary
  },
  emotion: {
    ...typography.title,
    color: colors.textPrimary,
    fontSize: 28
  },
  emotionGlyph: {
    alignItems: "center",
    borderRadius: radius.md,
    borderWidth: 1,
    height: 64,
    justifyContent: "center",
    width: 64
  },
  emotionGlyphText: {
    ...typography.title,
    fontSize: 26
  },
  emptyCopy: {
    flex: 1,
    gap: spacing.xxs
  },
  emptyGlyph: {
    alignItems: "center",
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    height: 56,
    justifyContent: "center",
    width: 56
  },
  emptyGlyphText: {
    ...typography.bodyStrong,
    color: colors.textMuted
  },
  emptyState: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md
  },
  emptySubtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  emptyTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  headerRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
    justifyContent: "space-between"
  },
  lastLogged: {
    ...typography.helper,
    color: colors.textMuted,
    flexShrink: 1
  },
  metaRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  snapshotCopy: {
    flex: 1,
    gap: spacing.sm
  },
  snapshotRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary
  },
  titleBlock: {
    flex: 1,
    gap: spacing.xxs
  }
});
