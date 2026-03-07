import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useNavigation } from "@react-navigation/native";

import { getFeatures } from "../api/features";
import type { FeatureRecord } from "../types/features";
import FeaturesPage from "./FeaturesPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useNavigation: jest.fn()
}));

const mockedGetFeatures = jest.mocked(getFeatures);
const mockedUseNavigation = jest.mocked(useNavigation);

const FEATURE_A: FeatureRecord = {
  createdAt: 1_772_800_000,
  data: {
    activity: { steps: 1200 },
    derived: { dayOfWeek: 2 }
  },
  id: "feature-a",
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
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
  });

  it("renders multiple feature records", async () => {
    mockedGetFeatures.mockResolvedValue([FEATURE_A, FEATURE_B]);

    const { getAllByText, getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Features")).toBeTruthy();
      expect(getAllByText(`Source: ${FEATURE_A.source}`)).toHaveLength(2);
      expect(getByText("Summary: 2 summary fields")).toBeTruthy();
      expect(getByText("Summary: 1 section")).toBeTruthy();
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
      expect(getByText("No feature captures yet")).toBeTruthy();
    });
  });

  it("renders error state when feature history fetch fails", async () => {
    mockedGetFeatures.mockRejectedValue(new Error("Failed to load feature history."));

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to load feature history.")).toBeTruthy();
      expect(getByText("Retry")).toBeTruthy();
    });
  });
});
