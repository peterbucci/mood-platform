import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useNavigation } from "@react-navigation/native";

import { getLatestFeature } from "../api/features";
import type { FeatureRecord } from "../types/features";
import DashboardPage from "./DashboardPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useNavigation: jest.fn()
}));

const mockedGetLatestFeature = jest.mocked(getLatestFeature);
const mockedUseNavigation = jest.mocked(useNavigation);

const LATEST_FEATURE: FeatureRecord = {
  createdAt: 1_772_800_900,
  data: {
    activity: {
      active_minutes: 38,
      steps: 4567
    },
    derived: {
      dayOfWeek: 2,
      isWeekend: false,
      rhrMean7d: 70
    },
    heart_rate: {
      resting_bpm: 61
    },
    hrv: {
      daily_rmssd: 35.2
    },
    meta: {
      extractor_version: "v2.1.0",
      source_timezone: "America/New_York",
      window_end: "2026-03-06T12:00:00Z",
      window_start: "2026-03-06T00:00:00Z"
    },
    personal_baseline: {
      avg_sleep: 410
    },
    sleep: {
      sleep_efficiency_pct: 91,
      total_sleep_minutes: 420
    }
  },
  id: "feature-1",
  label: {
    category: "energized",
    emotion: "Happy"
  },
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

describe("DashboardPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
  });

  it("renders grouped latest snapshot sections and metadata", async () => {
    mockedGetLatestFeature.mockResolvedValue(LATEST_FEATURE);

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("Dashboard")).toBeTruthy();
      expect(getByText("Activity")).toBeTruthy();
      expect(getByText("Heart / Recovery")).toBeTruthy();
      expect(getByText("Sleep")).toBeTruthy();
      expect(getByText("Daily / Context")).toBeTruthy();
      expect(getByText("Personal / Baseline")).toBeTruthy();
      expect(getByText("Snapshot Metadata")).toBeTruthy();
      expect(getByText("America/New_York")).toBeTruthy();
      expect(getByText("v2.1.0")).toBeTruthy();
      expect(getByText("Mood")).toBeTruthy();
      expect(getByText("Energized")).toBeTruthy();
      expect(getByText("- Happy")).toBeTruthy();
    });
  });

  it("renders empty state when no latest feature exists", async () => {
    mockedGetLatestFeature.mockResolvedValue(null);

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(
        getByText(
          "No feature data available yet. Request a capture to generate your first snapshot."
        )
      ).toBeTruthy();
    });
  });

  it("renders error state when latest feature fetch fails", async () => {
    mockedGetLatestFeature.mockRejectedValue(new Error("Failed to fetch latest feature snapshot."));

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to fetch latest feature snapshot.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });

  it("navigates to feature detail when detail link is tapped", async () => {
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({
      navigate
    } as never);
    mockedGetLatestFeature.mockResolvedValue(LATEST_FEATURE);

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("View Full Feature Details")).toBeTruthy();
    });

    fireEvent.press(getByText("View Full Feature Details"));

    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: "feature-1" });
  });
});
