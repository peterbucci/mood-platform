import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useIsFocused, useNavigation } from "@react-navigation/native";

import { getFeatures } from "../api/features";
import type { FeatureRecord } from "../types/features";
import FeaturesPage from "./FeaturesPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn(),
  useNavigation: jest.fn()
}));

const mockedGetFeatures = jest.mocked(getFeatures);
const mockedUseIsFocused = jest.mocked(useIsFocused);
const mockedUseNavigation = jest.mocked(useNavigation);

const FEATURE_A: FeatureRecord = {
  createdAt: 1_772_800_000,
  data: {
    activity: { steps: 1200 },
    derived: { dayOfWeek: 2 }
  },
  id: "feature-a",
  label: {
    category: "calm",
    emotion: "Relaxed"
  },
  source: "fitbit-pipeline",
  summaryMetadata: { quality: "good", completeness: 0.95 },
  userId: "00000000-0000-0000-0000-000000000001"
};

const FEATURE_B: FeatureRecord = {
  createdAt: 1_772_801_000,
  data: {
    sleep: { total_sleep_minutes: 410 }
  },
  id: "feature-b",
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

describe("FeaturesPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockedUseIsFocused.mockReturnValue(true);
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
  });

  it("renders multiple feature records", async () => {
    mockedGetFeatures.mockResolvedValue([FEATURE_A, FEATURE_B]);

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Features")).toBeTruthy();
      expect(getByText("Feature ID: feature-a")).toBeTruthy();
      expect(getByText("Feature ID: feature-b")).toBeTruthy();
      expect(getByText("Mood: Calm - Relaxed")).toBeTruthy();
      expect(getByText("Mood: Not labeled")).toBeTruthy();
    });
  });

  it("navigates to feature detail when row is tapped", async () => {
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({ navigate } as never);
    mockedGetFeatures.mockResolvedValue([FEATURE_A]);

    const { getByTestId } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByTestId("feature-row-feature-a")).toBeTruthy();
    });

    fireEvent.press(getByTestId("feature-row-feature-a"));

    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: "feature-a" });
  });

  it("renders empty state when no features exist", async () => {
    mockedGetFeatures.mockResolvedValue([]);

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("No feature captures yet. Request a capture to build your history.")).toBeTruthy();
    });
  });

  it("renders error state when feature history fetch fails", async () => {
    mockedGetFeatures.mockRejectedValue(new Error("Failed to load feature history."));

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to load feature history.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });
});
