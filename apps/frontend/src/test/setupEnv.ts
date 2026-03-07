if (!process.env.EXPO_PUBLIC_API_BASE_URL) {
  process.env.EXPO_PUBLIC_API_BASE_URL = "http://localhost:8000";
}

jest.mock("victory-native", () => {
  const React = require("react");
  const { View } = require("react-native");

  const MockComponent = ({ children, ...props }: Record<string, unknown> & { children?: unknown }) =>
    React.createElement(View, props, children);

  return {
    VictoryArea: MockComponent,
    VictoryAxis: MockComponent,
    VictoryChart: MockComponent,
    VictoryStack: MockComponent,
    VictoryTheme: {
      material: {}
    }
  };
});
