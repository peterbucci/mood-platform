import { fireEvent, render, waitFor } from "@testing-library/react-native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { createApiError } from "../api/errors";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import FeatureMoodLabelPage from "./FeatureMoodLabelPage";

jest.mock("../api/features");

const mockedGetFeatureById = jest.mocked(getFeatureById);
const mockedSetFeatureLabel = jest.mocked(setFeatureLabel);

const DETAIL_FEATURE: FeatureRecord = {
  createdAt: 1_772_800_000,
  data: {
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
  const navigation = {
    goBack: jest.fn(),
    navigate: jest.fn()
  } as never;

  return {
    navigation,
    route: {
      key: `FeatureMoodLabel-${id}`,
      name: "FeatureMoodLabel",
      params: { id }
    } as {
      key: string;
      name: "FeatureMoodLabel";
      params: RootStackParamList["FeatureMoodLabel"];
    }
  };
}

describe("FeatureMoodLabelPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("loads feature label and saves updates, then goes back", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    mockedSetFeatureLabel.mockResolvedValue({
      category: "stressed",
      emotion: "Anxious"
    });

    const props = makeProps("feature-detail-1");
    const { getAllByText, getByTestId, getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getAllByText("Update Mood Label").length).toBeGreaterThan(0);
      expect(getByText("Cancel")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-stressed"));
    fireEvent.press(getByTestId("mood-emotion-option-anxious"));
    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(mockedSetFeatureLabel).toHaveBeenCalledWith("feature-detail-1", "stressed", "Anxious");
      expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledTimes(1);
      expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledWith(
        "FeatureDetail",
        expect.objectContaining({ id: "feature-detail-1", refreshAt: expect.any(Number) })
      );
    });
  });

  it("goes back when Cancel is pressed", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const props = makeProps("feature-detail-1");
    const { getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getByText("Cancel")).toBeTruthy();
    });

    fireEvent.press(getByText("Cancel"));

    expect((props.navigation as never as { goBack: jest.Mock }).goBack).toHaveBeenCalledTimes(1);
  });

  it("renders not found state for missing feature id", async () => {
    mockedGetFeatureById.mockRejectedValue(
      createApiError({ message: "Feature not found.", status: 404 })
    );

    const props = makeProps("missing-feature");
    const { getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getByText("Feature missing-feature was not found.")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });
  });

  it("renders error state when loading fails", async () => {
    mockedGetFeatureById.mockRejectedValue(new Error("Unable to load feature."));

    const props = makeProps("feature-detail-1");
    const { getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Unable to load feature.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });
  });
});
