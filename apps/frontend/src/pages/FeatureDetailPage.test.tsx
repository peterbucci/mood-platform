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
    mockedUseIsFocused.mockReturnValue(true);
  });

  it("loads a feature by id and renders grouped detail with dropdown section navigation", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const props = makeProps("feature-detail-1");
    const { getAllByText, getByTestId, getByText, queryByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(mockedGetFeatureById).toHaveBeenCalledWith("feature-detail-1");
      expect(getAllByText("Activity").length).toBeGreaterThan(0);
      expect(getByText("Mood")).toBeTruthy();
      expect(getAllByText("Calm").length).toBeGreaterThan(0);
      expect(getByText("- Relaxed")).toBeTruthy();
      expect(getByText("Update Mood Label")).toBeTruthy();
    });

    expect(getByText("Steps Count")).toBeTruthy();
    expect(queryByText("Sleep Efficiency")).toBeNull();

    fireEvent.press(getByTestId("feature-detail-section-dropdown-toggle"));
    fireEvent.press(getByTestId("feature-detail-section-option-sleep"));
    expect(getAllByText("Sleep").length).toBeGreaterThan(0);
    expect(getByText("Sleep Efficiency")).toBeTruthy();

    fireEvent.press(getByTestId("feature-detail-section-dropdown-toggle"));
    fireEvent.press(getByTestId("feature-detail-section-option-metadata"));
    expect(getByText("Feature Metadata")).toBeTruthy();
    expect(getByText("fitbit-pipeline")).toBeTruthy();
    expect(getByText("America/New_York")).toBeTruthy();
  });

  it("shows Add Mood Label CTA when feature has no label", async () => {
    mockedGetFeatureById.mockResolvedValue(UNLABELED_FEATURE);

    const props = makeProps("feature-detail-unlabeled");
    const { getByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Mood")).toBeTruthy();
      expect(getByText("Not labeled")).toBeTruthy();
      expect(getByText("Add Mood Label")).toBeTruthy();
    });
  });

  it("navigates to mood editor screen from the bottom CTA", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    const props = makeProps("feature-detail-1");
    const { getByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByText("Update Mood Label")).toBeTruthy();
    });

    fireEvent.press(getByText("Update Mood Label"));

    expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledWith(
      "FeatureMoodLabel",
      { id: "feature-detail-1" }
    );
  });

  it("renders raw JSON directly when raw section is selected", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    const props = makeProps("feature-detail-1");
    const { getByTestId, getByText, queryByText } = render(<FeatureDetailPage {...props} />);

    await waitFor(() => {
      expect(getByTestId("feature-detail-section-dropdown-toggle")).toBeTruthy();
    });

    fireEvent.press(getByTestId("feature-detail-section-dropdown-toggle"));
    fireEvent.press(getByTestId("feature-detail-section-option-raw-json"));

    await waitFor(() => {
      expect(getByText(/"id": "feature-detail-1"/)).toBeTruthy();
    });
    expect(queryByText("Show Raw JSON")).toBeNull();
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
