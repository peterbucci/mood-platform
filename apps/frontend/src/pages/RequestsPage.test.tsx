import { act, fireEvent, render, waitFor, within } from "@testing-library/react-native";
import { useIsFocused, useNavigation } from "@react-navigation/native";

import { getFeatures } from "../api/features";
import {
  cancelRequest,
  createFeatureRequest,
  getPendingRequestCount,
  getRequests
} from "../api/requests";
import { DEFAULT_REQUEST_POLL_INTERVAL_MS } from "../hooks/useRequestPolling";
import type { FeatureRequestRecord } from "../types/requests";
import RequestsPage from "./RequestsPage";

jest.mock("../api/requests");
jest.mock("../api/features");
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn(),
  useNavigation: jest.fn()
}));

const mockedGetFeatures = jest.mocked(getFeatures);
const mockedCreateFeatureRequest = jest.mocked(createFeatureRequest);
const mockedCancelRequest = jest.mocked(cancelRequest);
const mockedGetPendingRequestCount = jest.mocked(getPendingRequestCount);
const mockedGetRequests = jest.mocked(getRequests);
const mockedUseIsFocused = jest.mocked(useIsFocused);
const mockedUseNavigation = jest.mocked(useNavigation);

const PENDING_REQUEST: FeatureRequestRecord = {
  createdAt: 1_772_800_000,
  featureId: null,
  id: "request-pending-1",
  source: "fitbit-pipeline",
  status: "pending",
  userId: "00000000-0000-0000-0000-000000000001"
};

const FULFILLED_REQUEST: FeatureRequestRecord = {
  createdAt: 1_772_800_100,
  featureId: "feature-fulfilled-1",
  id: "request-fulfilled-1",
  source: "fitbit-pipeline",
  status: "fulfilled",
  userId: "00000000-0000-0000-0000-000000000001"
};

const CANCELED_REQUEST: FeatureRequestRecord = {
  createdAt: 1_772_800_200,
  featureId: null,
  id: "request-canceled-1",
  source: "fitbit-pipeline",
  status: "canceled",
  userId: "00000000-0000-0000-0000-000000000001"
};

const FEATURE_FOR_FULFILLED = {
  createdAt: 1_772_800_100,
  data: { sleep: { total_sleep_minutes: 400 } },
  id: "feature-fulfilled-1",
  label: {
    category: "calm" as const,
    emotion: "Relaxed"
  },
  source: "fitbit-pipeline",
  userId: "00000000-0000-0000-0000-000000000001"
};

describe("RequestsPage", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-03-07T20:00:00Z"));
    jest.resetAllMocks();
    mockedUseIsFocused.mockReturnValue(true);
    mockedUseNavigation.mockReturnValue({
      navigate: jest.fn()
    } as never);
    mockedCreateFeatureRequest.mockResolvedValue({
      requestId: "request-created-1",
      status: "pending"
    });
    mockedCancelRequest.mockResolvedValue({
      ...PENDING_REQUEST,
      status: "canceled"
    });
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValue(1);
    mockedGetFeatures.mockResolvedValue([]);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders a cleaner summary and recent request activity", async () => {
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST, FULFILLED_REQUEST, CANCELED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValue(1);
    mockedGetFeatures.mockResolvedValue([FEATURE_FOR_FULFILLED]);

    const { getAllByText, getByText, getByTestId } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Requests")).toBeTruthy();
      expect(getByText("Capture a New Snapshot")).toBeTruthy();
      expect(getByText("Recent captures")).toBeTruthy();
      expect(getByText("Pending")).toBeTruthy();
      expect(getByText("Completed today")).toBeTruthy();
      expect(getByText("Last capture")).toBeTruthy();
      expect(getByText("In progress")).toBeTruthy();
      expect(getByText("Ready")).toBeTruthy();
      expect(getByText("Canceled")).toBeTruthy();
      expect(getByText("1 capture is processing. Updates appear automatically.")).toBeTruthy();
      expect(getByText("View feature details")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });

    expect(within(getByTestId(`request-item-${FULFILLED_REQUEST.id}`)).getByText("Relaxed")).toBeTruthy();
    expect(getAllByText("Mood not labeled").length).toBeGreaterThan(0);
  });

  it("shows the selected mood label on newly created pending requests", async () => {
    const createdRequestId = "request-created-1";
    mockedCreateFeatureRequest.mockResolvedValueOnce({
      requestId: createdRequestId,
      status: "pending"
    });
    mockedGetRequests
      .mockResolvedValueOnce([PENDING_REQUEST])
      .mockResolvedValueOnce([
        {
          ...PENDING_REQUEST,
          id: createdRequestId
        }
      ]);
    mockedGetPendingRequestCount.mockResolvedValue(1);

    const { getAllByText, getByTestId, getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByTestId("mood-category-option-calm")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-calm"));
    fireEvent.press(getByTestId("mood-emotion-option-relaxed"));
    fireEvent.press(getByTestId("log-emotion-button"));

    await waitFor(() => {
      expect(getByText(`ID ${createdRequestId}`)).toBeTruthy();
      expect(getAllByText("Relaxed").length).toBeGreaterThan(0);
    });
  });

  it("logs selected category and emotion when creating a request", async () => {
    const { getByTestId } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByTestId("mood-category-option-calm")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-calm"));
    fireEvent.press(getByTestId("mood-emotion-option-relaxed"));
    fireEvent.press(getByTestId("log-emotion-button"));

    await waitFor(() => {
      expect(mockedCreateFeatureRequest).toHaveBeenCalledWith({
        clientFeatures: {
          moodCategory: "calm",
          moodEmotion: "Relaxed"
        }
      });
    });
  });

  it("shows empty state when there are no requests", async () => {
    mockedGetRequests.mockResolvedValue([]);
    mockedGetPendingRequestCount.mockResolvedValue(0);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("No recent captures yet")).toBeTruthy();
      expect(getByText("Queue is up to date.")).toBeTruthy();
    });
  });

  it("shows an error state when requests fail to load", async () => {
    mockedGetRequests.mockRejectedValue(new Error("Unable to load request list."));

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Unable to load recent captures")).toBeTruthy();
      expect(getByText("Unable to load request list.")).toBeTruthy();
      expect(getByText("Try Again")).toBeTruthy();
    });
  });

  it("loads requests when the screen becomes focused", async () => {
    mockedUseIsFocused.mockReturnValue(false);
    const { rerender } = render(<RequestsPage />);

    expect(mockedGetRequests).not.toHaveBeenCalled();
    expect(mockedGetPendingRequestCount).not.toHaveBeenCalled();

    mockedUseIsFocused.mockReturnValue(true);
    rerender(<RequestsPage />);

    await waitFor(() => {
      expect(mockedGetRequests).toHaveBeenCalledTimes(1);
      expect(mockedGetPendingRequestCount).toHaveBeenCalledTimes(1);
    });
  });

  it("polls while pending and updates request to fulfilled", async () => {
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({ navigate } as never);

    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST]).mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("In progress")).toBeTruthy();
      expect(getByText("1 capture is processing. Updates appear automatically.")).toBeTruthy();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS);
    });

    await waitFor(() => {
      expect(mockedGetRequests).toHaveBeenCalledTimes(2);
      expect(getByText("Ready")).toBeTruthy();
      expect(getByText("View feature details")).toBeTruthy();
    });

    fireEvent.press(getByText("View feature details"));
    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: "feature-fulfilled-1" });
  });

  it("stops polling once all requests are terminal", async () => {
    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST]).mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByText, queryByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("In progress")).toBeTruthy();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS);
    });

    await waitFor(() => {
      expect(getByText("Ready")).toBeTruthy();
      expect(getByText("Queue is up to date.")).toBeTruthy();
      expect(queryByText("1 capture is processing. Updates appear automatically.")).toBeNull();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS * 3);
    });

    expect(mockedGetRequests).toHaveBeenCalledTimes(2);
    expect(mockedGetPendingRequestCount).toHaveBeenCalledTimes(2);
  });

  it("reconciles duplicate request ids without duplicate UI rows", async () => {
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST, { ...PENDING_REQUEST, status: "fulfilled" }]);
    mockedGetPendingRequestCount.mockResolvedValue(0);

    const { getAllByText, getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Ready")).toBeTruthy();
      expect(getAllByText(`ID ${PENDING_REQUEST.id}`)).toHaveLength(1);
    });
  });

  it("cancels a pending request and updates status to canceled", async () => {
    const { getByText, queryByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("In progress")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });

    fireEvent.press(getByText("Cancel"));

    await waitFor(() => {
      expect(mockedCancelRequest).toHaveBeenCalledWith(PENDING_REQUEST.id);
      expect(getByText("Canceled")).toBeTruthy();
      expect(queryByText("Cancel")).toBeNull();
    });
  });

  it("shows cancel error when backend rejects cancellation", async () => {
    mockedCancelRequest.mockRejectedValueOnce(new Error("Request cannot be canceled."));

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Cancel")).toBeTruthy();
    });

    fireEvent.press(getByText("Cancel"));

    await waitFor(() => {
      expect(getByText("Request cannot be canceled.")).toBeTruthy();
      expect(getByText("Cancel")).toBeTruthy();
    });
  });

  it("prevents repeated rapid cancellation taps", async () => {
    let resolveCancel:
      | ((value: FeatureRequestRecord | PromiseLike<FeatureRequestRecord>) => void)
      | undefined;
    mockedCancelRequest.mockImplementationOnce(
      () =>
        new Promise<FeatureRequestRecord>((resolve) => {
          resolveCancel = resolve;
        })
    );

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Cancel")).toBeTruthy();
    });

    const cancelButton = getByText("Cancel");
    fireEvent.press(cancelButton);
    fireEvent.press(cancelButton);

    expect(mockedCancelRequest).toHaveBeenCalledTimes(1);

    expect(resolveCancel).toBeDefined();
    resolveCancel?.({
      ...PENDING_REQUEST,
      status: "canceled"
    });

    await waitFor(() => {
      expect(getByText("Canceled")).toBeTruthy();
    });
  });
});
