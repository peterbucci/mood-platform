import type { ComponentType } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { SafeAreaProvider } from "react-native-safe-area-context";

import AppLayout from "../components/layout/AppLayout";
import DashboardPage from "../pages/DashboardPage";
import FeatureDetailPage from "../pages/FeatureDetailPage";
import FeatureMoodLabelPage from "../pages/FeatureMoodLabelPage";
import FeaturesPage from "../pages/FeaturesPage";
import NotFoundPage from "../pages/NotFoundPage";
import RequestsPage from "../pages/RequestsPage";
import SettingsPage from "../pages/SettingsPage";

export type RootStackParamList = {
  Dashboard: undefined;
  Requests: undefined;
  Features: undefined;
  FeatureDetail: { id: string; refreshAt?: number };
  FeatureMoodLabel: { id: string };
  Settings: undefined;
  NotFound: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const linking = {
  prefixes: ["mood-platform://", "http://localhost:19006"],
  config: {
    screens: {
      Dashboard: "dashboard",
      Requests: "requests",
      Features: "features",
      FeatureDetail: "features/:id",
      FeatureMoodLabel: "features/:id/mood-label",
      Settings: "settings",
      NotFound: "*"
    }
  }
};

function withAppLayout<P extends object>(PageComponent: ComponentType<P>) {
  return function WrappedPage(props: P) {
    return (
      <AppLayout>
        <PageComponent {...props} />
      </AppLayout>
    );
  };
}

const DashboardScreen = withAppLayout(DashboardPage);
const RequestsScreen = withAppLayout(RequestsPage);
const FeaturesScreen = withAppLayout(FeaturesPage);
const FeatureDetailScreen = withAppLayout(FeatureDetailPage);
const FeatureMoodLabelScreen = withAppLayout(FeatureMoodLabelPage);
const SettingsScreen = withAppLayout(SettingsPage);
const NotFoundScreen = withAppLayout(NotFoundPage);

export default function AppRouter() {
  return (
    <SafeAreaProvider>
      <NavigationContainer linking={linking}>
        <Stack.Navigator initialRouteName="Dashboard" screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Dashboard" component={DashboardScreen} />
          <Stack.Screen name="Requests" component={RequestsScreen} />
          <Stack.Screen name="Features" component={FeaturesScreen} />
          <Stack.Screen name="FeatureDetail" component={FeatureDetailScreen} />
          <Stack.Screen name="FeatureMoodLabel" component={FeatureMoodLabelScreen} />
          <Stack.Screen name="Settings" component={SettingsScreen} />
          <Stack.Screen name="NotFound" component={NotFoundScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
