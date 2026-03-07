import type { ReactNode } from "react";
import { useRoute } from "@react-navigation/native";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, spacing } from "../../theme";
import Header from "./Header";
import Navigation from "./Navigation";

type AppLayoutProps = {
  children: ReactNode;
};

export default function AppLayout({ children }: AppLayoutProps) {
  const route = useRoute();
  const currentRouteName = route.name;

  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.headerArea}>
        <Header currentRouteName={currentRouteName}>
          <Navigation currentRouteName={currentRouteName} />
        </Header>
      </View>
      <ScrollView contentContainerStyle={styles.pageContainer}>
        <View style={styles.pageContent}>{children}</View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: colors.background,
    flex: 1
  },
  headerArea: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm
  },
  pageContainer: {
    alignItems: "center",
    padding: spacing.xl,
    paddingBottom: spacing.xxl
  },
  pageContent: {
    maxWidth: 900,
    rowGap: spacing.md,
    width: "100%"
  }
});
