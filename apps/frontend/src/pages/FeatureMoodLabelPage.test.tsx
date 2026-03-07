import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { useIsFocused } from "@react-navigation/native";

import { getFeatureById, setFeatureLabel } from "../api/features";
import { createApiError } from "../api/errors";
import type { RootStackParamList } from "../router/AppRouter";
import type { FeatureRecord } from "../types/features";
import FeatureMoodLabelPage from "./FeatureMoodLabelPage";

jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn()
}));

const mockedGetFeatureById = jest.mocked(getFeatureById);
const mockedSetFeatureLabel = jest.mocked(setFeatureLabel);
const mockedUseIsFocused = jest.mocked(useIsFocused);

const FEATURE_ID = "95776547-ffb2-400f-8320-b62d9f42d470";

const DETAIL_FEATURE: FeatureRecord = {
  createdAt: 1_772_800_000,
  data: {
    sleep: {
      sleep_efficiency: 91
    }
  },
  extractorVersion: "v3.2.1",
  id: FEATURE_ID,
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
    mockedUseIsFocused.mockReturnValue(true);
  });

  it("loads snapshot context, updates the preview, and saves the label", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);
    mockedSetFeatureLabel.mockResolvedValue({
      category: "stressed",
      emotion: "Anxious"
    });

    const props = makeProps(FEATURE_ID);
    const { getAllByText, getByTestId, getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getByText("Update Mood Label")).toBeTruthy();
      expect(getByText("Feature Snapshot")).toBeTruthy();
      expect(getByText("Mood Preview")).toBeTruthy();
      expect(getByText("Mood Selection")).toBeTruthy();
      expect(getByText("9577...d470")).toBeTruthy();
      expect(getByText("Source: Fitbit")).toBeTruthy();
      expect(getAllByText("Relaxed").length).toBeGreaterThan(0);
      expect(getByText("Save Label")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-stressed"));
    fireEvent.press(getByTestId("mood-emotion-option-anxious"));

    await waitFor(() => {
      expect(getAllByText("Stressed").length).toBeGreaterThan(0);
      expect(getAllByText("Anxious").length).toBeGreaterThan(0);
    });

    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(mockedSetFeatureLabel).toHaveBeenCalledWith(FEATURE_ID, "stressed", "Anxious");
      expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledTimes(1);
      expect((props.navigation as never as { navigate: jest.Mock }).navigate).toHaveBeenCalledWith(
        "FeatureDetail",
        expect.objectContaining({ id: FEATURE_ID, refreshAt: expect.any(Number) })
      );
    });
  });

  it("goes back when Cancel is pressed", async () => {
    mockedGetFeatureById.mockResolvedValue(DETAIL_FEATURE);

    const props = makeProps(FEATURE_ID);
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

    const props = makeProps(FEATURE_ID);
    const { getByText } = render(<FeatureMoodLabelPage {...props} />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Unable to load feature.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });
  });
});
