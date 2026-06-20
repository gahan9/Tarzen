// SPDX-License-Identifier: MIT
/**
 * Carbon Footprint mobile app root.
 *
 * Composes the provider stack (Auth -> Consent -> offline Queue) and a bottom-
 * tab navigator with the Log and History screens. Configures the (gated) push
 * nudge handler on mount. Runs fully offline out of the box via the mock API
 * (see `config/env.ts`).
 */

import { useEffect } from "react";
import { StyleSheet } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { StatusBar } from "expo-status-bar";

import { AuthProvider } from "./src/auth/AuthContext";
import { ConsentProvider } from "./src/capture/ConsentContext";
import { configureNudgeHandler } from "./src/nudges/push";
import { QueueProvider } from "./src/offline/QueueContext";
import { HistoryScreen } from "./src/screens/HistoryScreen";
import { LogScreen } from "./src/screens/LogScreen";

const Tab = createBottomTabNavigator();

export default function App() {
  useEffect(() => {
    configureNudgeHandler();
  }, []);

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <ConsentProvider>
          <QueueProvider>
            <NavigationContainer>
              <StatusBar style="dark" />
              <Tab.Navigator
                screenOptions={{
                  headerStyle: styles.header,
                  headerTitleStyle: styles.headerTitle,
                  tabBarActiveTintColor: "#0f6b46",
                }}
              >
                <Tab.Screen
                  name="Log"
                  component={LogScreen}
                  options={{ title: "Log a trip" }}
                />
                <Tab.Screen
                  name="History"
                  component={HistoryScreen}
                  options={{ title: "History & insights" }}
                />
              </Tab.Navigator>
            </NavigationContainer>
          </QueueProvider>
        </ConsentProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  header: { backgroundColor: "#0f6b46" },
  headerTitle: { color: "#ffffff" },
});
