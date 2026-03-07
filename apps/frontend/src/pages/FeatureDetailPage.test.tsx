import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useIsFocused } from "@react-navigation/native";

import { getFeatureById } from "../api/features";
import { createApiError } from "../api/errors";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import FeatureDetailPage from "./FeatureDetailPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn()
}));

const mockedGetFeatureById = jest.mocked(getFeatureById);
const mockedUseIsFocused = jest.mocked(useIsFocused);

function toSeconds(value: string): number {
  return Math.floor(new Date(value).getTime() / 1000);
}

const DETAIL_FEATURE: FeatureRecord = {
  createdAt: toSeconds("2026-03-07T18:05:00Z"),
  data: {
    activity: {
      active_zone_minutes: 69,
      calories_out_kcal: 906,
      steps_count: 4567
    },
    derived: {
      day_of_week: 6,
      weekday_flag: false
    },
    heart_rate: {
      resting_hr: 62
    },
    personal_baseline: {
      hrv_mean: 35.2
    },
    sleep: {
      sleep_efficiency: 91,
      total_sleep_minutes: 423
    }
  },
  extractorVersion: "v3.2.1",
  id: "feature-detail-1",
  label: {
    category: "calm",
    emotion: "Relaxed"
  },
  source: "fitbit-pipeline",
  sourceTimezone: "America/New_York",
  userId: "00000000-0000-0000-0000-000000000001",
  windowEnd: "2026-03-07T12:00:00Z",
  windowStart: "2026-03-07T00:00:00Z"
};

const UNLABELED_FEATURE: FeatureRecord = {
  ...DETAIL_FEATURE,
  id: "feature-detail-unlabeled",
  label: undefined
};

function makeProps(id: string) {
  const navigation = {
    navigate: jest.fn()
  } as never;

  return {
    navigation,
    route: {
      key: `FeatureDetail-${id}`,
      name: "FeatureDetail",
      params: { id }
    } as {
      key: string;
      name: "FeatureDetail";
      params: RootStackParamList["FeatureDetail"];
    }
  };
}

describe("FeatureDetailPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-07T20:05:00Z"));
    mockedUseIsFocused.mockReturnValue(true);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("loads a feature by id and renders summary-first detail with section tabs", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const props = makeProps("feature-detail-1");
    const { getAllByText, getByTestId, getByText, queryByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(mockedGetFeatureById).toHaveBeenCalledWith("feature-detail-1");
      expect(getByText("Snapshot Summary")).toBeTruthy();
      expect(getByText("Key Metrics")).toBeTruthy();
      expect(getByText("Detailed Sections")).toBeTruthy();
      expect(getByText("Metadata")).toBeTruthy();
      expect(getAllByText("Calm").length).toBeGreaterThan(0);
      expect(getByText("Relaxed")).toBeTruthy();
      expect(getByText("Captured after a recent Fitbit sync.")).toBeTruthy();
      expect(getByText("7h 03m")).toBeTruthy();
      expect(getAllByText("4,567").length).toBeGreaterThan(0);
      expect(getAllByText("62 bpm").length).toBeGreaterThan(0);
      expect(getAllByText("906 kcal").length).toBeGreaterThan(0);
      expect(getAllByText("Fitbit").length).toBeGreaterThan(0);
    });

    expect(getAllByText("Activity").length).toBeGreaterThan(0);
    expect(getAllByText("Steps").length).toBeGreaterThan(0);
    expect(getByText("Movement, activity, and exertion signals from this snapshot.")).toBeTruthy();
    expect(queryByText("Sleep-related signals that help explain the snapshot context.")).toBeNull();

    fireEvent.press(getByTestId("feature-detail-section-tab-sleep"));

    await waitFor(() => {
      expect(getAllByText("Sleep").length).toBeGreaterThan(0);
      expect(getByText("Sleep-related signals that help explain the snapshot context.")).toBeTruthy();
      expect(getAllByText("Sleep Efficiency").length).toBeGreaterThan(0);
      expect(getAllByText("91%").length).toBeGreaterThan(0);
    });
  });

  it("shows Add Mood Label CTA when feature has no label", async () => {
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);

    const props = makeProps("feature-detail-unlabeled");
    const { getByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Snapshot Summary")).toBeTruthy();
      expect(getByText("Not labeled")).toBeTruthy();
      expect(getByText("Add Mood Label")).toBeTruthy();
    });
  });

  it("navigates to mood editor screen from the summary card action", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    const props = makeProps("feature-detail-1");
    const { getByTestId } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByTestId("feature-detail-mood-action")).toBeTruthy();
    });

    fireEvent.press(getByTestId("feature-detail-mood-action"));

    expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledWith(
      "FeatureMoodLabel",
      { id: "feature-detail-1" }
    );
  });

  it("keeps raw JSON collapsed until the debug toggle is opened", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    const props = makeProps("feature-detail-1");
    const { getByTestId, getByText, queryByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Debug Data")).toBeTruthy();
      expect(getByTestId("feature-detail-raw-json-toggle")).toBeTruthy();
    });

    expect(queryByText(/"id": "feature-detail-1"/)).toBeNull();

    fireEvent.press(getByTestId("feature-detail-raw-json-toggle"));

    await waitFor(() => {
      expect(getByText(/"id": "feature-detail-1"/)).toBeTruthy();
    });
  });

  it("renders a not found state when feature id does not resolve", async () => {
    mockedGetFeatureById.mockRejectedValue(
      createApiError({ message: "Feature not found.", status: 404 })
    );

    const props = makeProps("missing-feature");
    const { getByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Feature missing-feature was not found.")).toBeTruthy();
    });
  });

  it("renders error state when feature detail request fails", async () => {
    mockedGetFeatureById.mockRejectedValue(new Error("Failed to load feature detail."));

    const props = makeProps("feature-detail-1");
    const { getByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to load feature detail.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });
});
