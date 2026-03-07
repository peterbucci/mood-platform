import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useIsFocused, useNavigation } from "@react-navigation/native";

import { getFeatures } from "../api/features";
import type { FeatureRecord } from "../types/features";
import type { MoodCategory } from "../types/mood";
import DashboardPage from "./DashboardPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn(),
  useNavigation: jest.fn()
}));

const mockedGetFeatures = jest.mocked(getFeatures);
const mockedUseIsFocused = jest.mocked(useIsFocused);
const mockedUseNavigation = jest.mocked(useNavigation);

function toEpoch(value: string): number {
  return Math.floor(new Date(value).getTime() / 1000);
}

function buildFeature(
  id: string,
  createdAt: string,
  category?: MoodCategory,
  emotion?: string
): FeatureRecord {
  return {
    id,
    userId: "00000000-0000-0000-0000-000000000001",
    createdAt: toEpoch(createdAt),
    source: "fitbit-pipeline",
    data: {},
    label: category && emotion ? { category, emotion } : undefined
  };
}

const FEATURE_HISTORY: FeatureRecord[] = [
  buildFeature("feature-1", "2026-03-01T18:00:00Z", "calm", "Relaxed"),
  buildFeature("feature-2", "2026-03-02T18:00:00Z", "energized", "Motivated"),
  buildFeature("feature-3", "2026-03-03T18:00:00Z", "energized", "Motivated"),
  buildFeature("feature-4", "2026-03-05T18:00:00Z", "stressed", "Anxious"),
  buildFeature("feature-5", "2026-03-07T12:00:00Z", "calm", "Relaxed"),
  buildFeature("feature-6", "2026-03-07T18:00:00Z", "energized", "Motivated")
];

describe("DashboardPage", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-07T20:00:00Z"));
    jest.resetAllMocks();

    mockedUseIsFocused.mockReturnValue(true);
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders the dashboard overview and supports chart toggles", async () => {
    mockedGetFeatures.mockResolvedValue(FEATURE_HISTORY);

    const { getAllByText, getByTestId, getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("Today's Mood")).toBeTruthy();
      expect(getAllByText("Motivated").length).toBeGreaterThan(0);
      expect(getByText("2 entries today")).toBeTruthy();
      expect(getByText("Entries this week")).toBeTruthy();
      expect(getByText("Most common mood")).toBeTruthy();
      expect(getByText("Average category")).toBeTruthy();
      expect(getByText("Longest streak")).toBeTruthy();
      expect(getByText("Mood Trend")).toBeTruthy();
      expect(getByText("Category Distribution")).toBeTruthy();
      expect(getByText("Insights")).toBeTruthy();
      expect(getByText("View details for the latest feature set")).toBeTruthy();
      expect(getByText("Last logged 2h ago")).toBeTruthy();
      expect(getByTestId("mood-history-chart")).toBeTruthy();
    });

    fireEvent.press(getByTestId("dashboard-timeframe-14"));

    await waitFor(() => {
      expect(getByText("Daily stacked trend for the last 14 days.")).toBeTruthy();
      expect(getByText("Last 14 days")).toBeTruthy();
    });

    fireEvent.press(getByTestId("dashboard-mode-emotion"));

    await waitFor(() => {
      expect(getByText("Anxious")).toBeTruthy();
      expect(getAllByText("Relaxed").length).toBeGreaterThan(0);
    });
  });

  it("renders an empty feature state when there is no dashboard data yet", async () => {
    mockedGetFeatures.mockResolvedValue([]);

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(
        getByText("No feature data available yet. Log an emotion to build your dashboard trend.")
      ).toBeTruthy();
    });
  });

  it("renders a no-label fallback when features exist without mood labels", async () => {
    mockedGetFeatures.mockResolvedValue([buildFeature("feature-unlabeled", "2026-03-07T18:00:00Z")]);

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("No mood logged yet")).toBeTruthy();
      expect(
        getByText("No mood labels yet. Add labels on feature detail pages to populate this dashboard.")
      ).toBeTruthy();
      expect(getByText("View details for the latest feature set")).toBeTruthy();
    });
  });

  it("renders an error state when dashboard loading fails", async () => {
    mockedGetFeatures.mockRejectedValue(new Error("Failed to load dashboard overview."));

    const { getByText } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to load dashboard overview.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });

  it("uses the latest feature link to navigate to feature detail", async () => {
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({ navigate } as never);
    mockedGetFeatures.mockResolvedValue(FEATURE_HISTORY);

    const { getByTestId } = render(<DashboardPage />);

    await waitFor(() => {
      expect(getByTestId("dashboard-latest-feature-link")).toBeTruthy();
    });

    fireEvent.press(getByTestId("dashboard-latest-feature-link"));

    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: "feature-6" });
  });
});
