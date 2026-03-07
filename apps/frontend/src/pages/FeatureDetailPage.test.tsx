import { fireEvent, render, waitFor } from "@testing-library/react-native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { createApiError } from "../api/errors";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import FeatureDetailPage from "./FeatureDetailPage";

jest.mock("../api/features");

const mockedGetFeatureById = jest.mocked(getFeatureById);
const mockedSetFeatureLabel = jest.mocked(setFeatureLabel);

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

const UNLABELED_FEATURE: FeatureRecord = {
  ...DETAIL_FEATURE,
  id: "feature-detail-unlabeled",
  label: undefined
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
    mockedSetFeatureLabel.mockResolvedValue({
      category: "calm",
      emotion: "Relaxed"
    });
  });

  it("loads a feature by id and renders readable grouped detail", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const { getAllByText, getByText } = render(<FeatureDetailPage {...makeProps("feature-detail-1")} />);

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
      expect(getAllByText("Calm").length).toBeGreaterThan(0);
      expect(getByText("- Relaxed")).toBeTruthy();
      expect(getByText("Selected Category: Calm")).toBeTruthy();
      expect(getByText("Selected Emotion: Relaxed")).toBeTruthy();
    });
  });

  it("shows empty label form state for unlabeled features", async () => {
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);

    const { getByText } = render(
      <FeatureDetailPage {...makeProps("feature-detail-unlabeled")} />
    );

    await waitFor(() => {
      expect(getByText("Mood")).toBeTruthy();
      expect(getByText("Not labeled")).toBeTruthy();
      expect(getByText("Selected Category: Not selected")).toBeTruthy();
      expect(getByText("Selected Emotion: Not selected")).toBeTruthy();
    });
  });

  it("selects category/emotion and saves mood label through API", async () => {
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);
    mockedSetFeatureLabel.mockResolvedValue({
      category: "stressed",
      emotion: "Anxious"
    });

    const { getAllByText, getByTestId, getByText } = render(
      <FeatureDetailPage {...makeProps("feature-detail-unlabeled")} />
    );

    await waitFor(() => {
      expect(getByText("Add Mood Label")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-stressed"));
    fireEvent.press(getByTestId("mood-emotion-option-anxious"));
    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(mockedSetFeatureLabel).toHaveBeenCalledWith(
        "feature-detail-unlabeled",
        "stressed",
        "Anxious"
      );
      expect(getAllByText("Stressed").length).toBeGreaterThan(0);
      expect(getByText("- Anxious")).toBeTruthy();
    });
  });

  it("prevents duplicate save submissions while save is in flight", async () => {
    let resolveSave: (() => void) | null = null;
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);
    mockedSetFeatureLabel.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSave = () => resolve({ category: "calm", emotion: "Calm" });
        })
    );

    const { getByTestId, getByText } = render(
      <FeatureDetailPage {...makeProps("feature-detail-unlabeled")} />
    );

    await waitFor(() => {
      expect(getByText("Add Mood Label")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-calm"));
    fireEvent.press(getByTestId("mood-save-button"));
    fireEvent.press(getByTestId("mood-save-button"));

    expect(mockedSetFeatureLabel).toHaveBeenCalledTimes(1);

    resolveSave?.();

    await waitFor(() => {
      expect(getByText("- Calm")).toBeTruthy();
      expect(getByText("Selected Category: Calm")).toBeTruthy();
    });
  });

  it("shows API error if saving mood label fails", async () => {
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);
    mockedSetFeatureLabel.mockRejectedValue(new Error("Unable to save mood label."));

    const { getByTestId, getByText } = render(
      <FeatureDetailPage {...makeProps("feature-detail-unlabeled")} />
    );

    await waitFor(() => {
      expect(getByText("Add Mood Label")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-tired"));
    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(getByText("Unable to save mood label.")).toBeTruthy();
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
      expect(getByText("Try Again")).toBeTruthy();
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
