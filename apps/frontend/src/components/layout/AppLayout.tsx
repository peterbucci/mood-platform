import type { ReactNode } from "react";
import { useRoute } from "@react-navigation/native";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

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
    backgroundColor: "#f9fafb",
    flex: 1
  },
  headerArea: {
    backgroundColor: "#ffffff",
    paddingHorizontal: 20,
    paddingTop: 8
  },
  pageContainer: {
    alignItems: "center",
    padding: 20
  },
  pageContent: {
    maxWidth: 900,
    rowGap: 12,
    width: "100%"
  }
});
