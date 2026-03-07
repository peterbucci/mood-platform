import { useNavigation } from "@react-navigation/native";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../../theme";

type NavigationProps = {
  currentRouteName?: string;
};

const LINKS = [
  { routeName: "Dashboard", label: "Dashboard" },
  { routeName: "Requests", label: "Requests" },
  { routeName: "Features", label: "Features" },
  { routeName: "Settings", label: "Settings" }
] as const;

export default function Navigation({ currentRouteName }: NavigationProps) {
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      {LINKS.map((link) => {
        const isActive = currentRouteName === link.routeName;
        return (
          <Pressable
            key={link.routeName}
            accessibilityRole="button"
            onPress={() => navigation.navigate(link.routeName as never)}
            style={[styles.link, isActive ? styles.linkActive : null]}
          >
            <Text style={[styles.linkLabel, isActive ? styles.linkLabelActive : null]}>
              {link.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  link: {
    backgroundColor: colors.neutralSurface,
    borderColor: colors.neutralBorder,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 34,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs
  },
  linkActive: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary
  },
  linkLabel: {
    ...typography.bodyStrong,
    color: colors.textSecondary
  },
  linkLabelActive: {
    color: colors.inverseText
  }
});
