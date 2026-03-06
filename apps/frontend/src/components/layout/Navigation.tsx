import { useNavigation } from "@react-navigation/native";
import { Pressable, StyleSheet, Text, View } from "react-native";

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
    gap: 10
  },
  link: {
    backgroundColor: "#f3f4f6",
    borderColor: "#d1d5db",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6
  },
  linkActive: {
    backgroundColor: "#111827",
    borderColor: "#111827"
  },
  linkLabel: {
    color: "#1f2937",
    fontSize: 14,
    fontWeight: "600"
  },
  linkLabelActive: {
    color: "#ffffff"
  }
});
