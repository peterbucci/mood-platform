import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../../theme";

type RequestMetaRowProps = {
  items: string[];
};

export default function RequestMetaRow({ items }: RequestMetaRowProps) {
  const visibleItems = items.filter((item) => item.trim().length > 0);

  if (visibleItems.length === 0) {
    return null;
  }

  return (
    <View style={styles.row}>
      {visibleItems.map((item, index) => (
        <Text key={`${item}-${index}`} style={styles.item}>
          {item}
          {index < visibleItems.length - 1 ? " |" : ""}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  item: {
    ...typography.helper,
    color: colors.textMuted
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs
  }
});
