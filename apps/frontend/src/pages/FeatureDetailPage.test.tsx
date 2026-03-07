import { fireEvent, render, waitFor } from "@testing-library/react-native";

import { getFeatureById } from "../api/features";
import { createApiError } from "../api/errors";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import FeatureDetailPage from "./FeatureDetailPage";

jest.mock("../api/features");

const mockedGetFeatureById = jest.mocked(getFeatureById);

const DETAIL_FEATURE: FeatureRecord = {
  createdAt: 1_772_800_000,
  data: {
    activity: {
      steps_count: 4567
    },
    derived: {
      day_of_week: 2,
      weekday_flag: true
    },
    heart_rate: {
      resting_hr: 62
    },
    personal_baseline: {
      hrv_mean: 35.2
    },
    sleep: {
      sleep_efficiency: 91
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

function makeProps(id: string) {
  return {
    navigation: {} as never,
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
  });

  it("loads a feature by id and renders readable grouped detail", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const { getByText } = render(<FeatureDetailPage {...makeProps("feature-detail-1")} />);

    await waitFor(() => {
      expect(mockedGetFeatureById).toHaveBeenCalledWith("feature-detail-1");
      expect(getByText("Feature Metadata")).toBeTruthy();
      expect(getByText("Activity")).toBeTruthy();
      expect(getByText("Heart / Recovery")).toBeTruthy();
      expect(getByText("Sleep")).toBeTruthy();
      expect(getByText("Daily / Context")).toBeTruthy();
      expect(getByText("Personal / Baseline")).toBeTruthy();
      expect(getByText("Resting Heart Rate")).toBeTruthy();
      expect(getByText("Sleep Efficiency")).toBeTruthy();
      expect(getByText("Weekday Indicator")).toBeTruthy();
      expect(getByText("fitbit-pipeline")).toBeTruthy();
      expect(getByText("America/New_York")).toBeTruthy();
      expect(getByText("Mood")).toBeTruthy();
      expect(getByText("Calm")).toBeTruthy();
      expect(getByText("— Relaxed")).toBeTruthy();
    });
  });

  it("renders a not found state when feature id does not resolve", async () => {
    mockedGetFeatureById.mockRejectedValue(
      createApiError({ message: "Feature not found.", status: 404 })
    );

    const { getByText } = render(<FeatureDetailPage {...makeProps("missing-feature")} />);

    await waitFor(() => {
      expect(getByText("Feature missing-feature was not found.")).toBeTruthy();
    });
  });

  it("renders error state when feature detail request fails", async () => {
    mockedGetFeatureById.mockRejectedValue(new Error("Failed to load feature detail."));

    const { getByText } = render(<FeatureDetailPage {...makeProps("feature-detail-1")} />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Failed to load feature detail.")).toBeTruthy();
      expect(getByText("Retry")).toBeTruthy();
    });
  });

  it("toggles raw JSON view", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const { getByText, queryByText } = render(
      <FeatureDetailPage {...makeProps("feature-detail-1")} />
    );

    await waitFor(() => {
      expect(getByText("Show Raw JSON")).toBeTruthy();
    });

    expect(queryByText(/"id": "feature-detail-1"/)).toBeNull();

    fireEvent.press(getByText("Show Raw JSON"));

    await waitFor(() => {
      expect(getByText("Hide Raw JSON")).toBeTruthy();
      expect(getByText(/"id": "feature-detail-1"/)).toBeTruthy();
    });
  });
});
