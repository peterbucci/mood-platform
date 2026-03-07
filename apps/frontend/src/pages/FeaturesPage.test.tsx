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

function toSeconds(value: string): number {
  return Math.floor(new Date(value).getTime() / 1000);
}

const FEATURE_A: FeatureRecord = {
  createdAt: toSeconds("2026-03-07T18:00:00Z"),
  data: {
    activity: { steps: 1200 },
    derived: { dayOfWeek: 2 }
  },
  id: "95776547-ffb2-400f-8320-b62d9f42d470",
  label: {
    category: "energized",
    emotion: "Cheerful"
  },
  source: "fitbit-pipeline",
  summaryMetadata: { quality: "good", completeness: 0.95 },
  userId: "00000000-0000-0000-0000-000000000001"
};

const FEATURE_B: FeatureRecord = {
  createdAt: toSeconds("2026-03-07T12:00:00Z"),
  data: {
    sleep: { total_sleep_minutes: 410 }
  },
  id: "b41cc562-8dab-4b43-9933-fcb2724986f1",
  label: {
    category: "calm",
    emotion: "Relaxed"
  },
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

const FEATURE_C: FeatureRecord = {
  createdAt: toSeconds("2026-03-06T15:30:00Z"),
  data: {
    readiness: { score: 72 }
  },
  id: "0c08a1f8-8ae3-4940-b94d-bf3f0d92f4ac",
  label: {
    category: "calm",
    emotion: "Peaceful"
  },
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

const FEATURE_D: FeatureRecord = {
  createdAt: toSeconds("2026-03-04T09:15:00Z"),
  data: {
    sleep: { total_sleep_minutes: 390 }
  },
  id: "96da332e-0e10-4e4c-a1d1-9872fb84cb18",
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

describe("FeaturesPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-07T20:00:00Z"));
    mockedUseIsFocused.mockReturnValue(true);
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders grouped feature history with compact summaries", async () => {
    mockedGetFeatures.mockResolvedValue([FEATURE_A, FEATURE_B, FEATURE_C, FEATURE_D]);

    const { getAllByText, getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Features")).toBeTruthy();
      expect(getByText("Total captures")).toBeTruthy();
      expect(getByText("Last capture")).toBeTruthy();
      expect(getByText("Recent category")).toBeTruthy();
      expect(getByText("Capture history")).toBeTruthy();
      expect(getByText("Today")).toBeTruthy();
      expect(getByText("Yesterday")).toBeTruthy();
      expect(getByText("Cheerful")).toBeTruthy();
      expect(getByText("Relaxed")).toBeTruthy();
      expect(getAllByText("Not labeled").length).toBeGreaterThan(0);
      expect(getAllByText("2h ago").length).toBeGreaterThan(0);
      expect(getByText("4")).toBeTruthy();
      expect(getAllByText("Calm").length).toBeGreaterThan(0);
      expect(getByText(/ID 9577\.\.\.d470/)).toBeTruthy();
      expect(getAllByText("View details").length).toBeGreaterThan(0);
    });
  });

  it("navigates to feature detail when row is tapped", async () => {
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({ navigate } as never);
    mockedGetFeatures.mockResolvedValue([FEATURE_A]);

    const { getByTestId } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByTestId(`feature-history-item-${FEATURE_A.id}`)).toBeTruthy();
    });

    fireEvent.press(getByTestId(`feature-history-item-${FEATURE_A.id}`));

    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: FEATURE_A.id });
  });

  it("renders empty state when no features exist", async () => {
    mockedGetFeatures.mockResolvedValue([]);

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("No feature captures yet")).toBeTruthy();
      expect(getByText("Log an emotion to generate your first capture.")).toBeTruthy();
    });
  });

  it("renders error state when feature history fetch fails", async () => {
    mockedGetFeatures.mockRejectedValue(new Error("Failed to load feature history."));

    const { getByText } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByText("Unable to load feature history")).toBeTruthy();
      expect(getByText("Failed to load feature history.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });

  it("refreshes feature history from the header action", async () => {
    mockedGetFeatures.mockResolvedValue([FEATURE_A]);

    const { getByTestId } = render(<FeaturesPage />);

    await waitFor(() => {
      expect(getByTestId("features-refresh-button")).toBeTruthy();
      expect(mockedGetFeatures).toHaveBeenCalledTimes(1);
    });

    fireEvent.press(getByTestId("features-refresh-button"));

    await waitFor(() => {
      expect(mockedGetFeatures).toHaveBeenCalledTimes(2);
    });
  });
});
