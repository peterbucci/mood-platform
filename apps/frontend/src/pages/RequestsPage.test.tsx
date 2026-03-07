import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import { useIsFocused, useNavigation } from "@react-navigation/native";

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
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useIsFocused: jest.fn(),
  useNavigation: jest.fn()
}));

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

describe("RequestsPage", () => {
  beforeEach(() => {
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
  });

  it("renders pending, fulfilled, and canceled request statuses", async () => {
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST, FULFILLED_REQUEST, CANCELED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValue(1);

    const { getByText, queryAllByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(getByText("Canceled")).toBeTruthy();
      expect(getByText("Feature ID: feature-fulfilled-1")).toBeTruthy();
      expect(getByText("Cancel Request")).toBeTruthy();
      expect(queryAllByText("Cancel Request")).toHaveLength(1);
    });
  });

  it("shows empty state when there are no requests", async () => {
    mockedGetRequests.mockResolvedValue([]);
    mockedGetPendingRequestCount.mockResolvedValue(0);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(
        getByText("No feature requests yet. Trigger a capture to get started.")
      ).toBeTruthy();
    });
  });

  it("shows an error state when requests fail to load", async () => {
    mockedGetRequests.mockRejectedValue(new Error("Unable to load request list."));

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
      expect(getByText("Unable to load request list.")).toBeTruthy();
      expect(getByText("Retry")).toBeTruthy();
    });
  });

  it("refreshes requests and pending count when refresh is tapped", async () => {
    mockedGetRequests
      .mockResolvedValueOnce([PENDING_REQUEST])
      .mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByText, getByTestId } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
      expect(getByTestId("pending-count-value").props.children).toBe(1);
    });

    fireEvent.press(getByText("Refresh"));

    await waitFor(() => {
      expect(mockedGetRequests).toHaveBeenCalledTimes(2);
      expect(mockedGetPendingRequestCount).toHaveBeenCalledTimes(2);
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(getByTestId("pending-count-value").props.children).toBe(0);
    });
  });

  it("polls while pending and updates request to fulfilled", async () => {
    jest.useFakeTimers();
    const navigate = jest.fn();
    mockedUseNavigation.mockReturnValue({ navigate } as never);

    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST]).mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
      expect(getByText("Auto-refreshing pending requests every few seconds...")).toBeTruthy();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS);
    });

    await waitFor(() => {
      expect(mockedGetRequests).toHaveBeenCalledTimes(2);
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(getByText("View Feature")).toBeTruthy();
    });

    fireEvent.press(getByText("View Feature"));
    expect(navigate).toHaveBeenCalledWith("FeatureDetail", { id: "feature-fulfilled-1" });

    jest.useRealTimers();
  });

  it("stops polling once all requests are terminal", async () => {
    jest.useFakeTimers();

    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST]).mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByText, queryByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS);
    });

    await waitFor(() => {
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(queryByText("Auto-refreshing pending requests every few seconds...")).toBeNull();
    });

    act(() => {
      jest.advanceTimersByTime(DEFAULT_REQUEST_POLL_INTERVAL_MS * 3);
    });

    expect(mockedGetRequests).toHaveBeenCalledTimes(2);
    expect(mockedGetPendingRequestCount).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });

  it("reconciles duplicate request ids without duplicate UI rows", async () => {
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST, { ...PENDING_REQUEST, status: "fulfilled" }]);
    mockedGetPendingRequestCount.mockResolvedValue(0);

    const { getAllByText, getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(getAllByText(`Request ID: ${PENDING_REQUEST.id}`)).toHaveLength(1);
    });
  });

  it("cancels a pending request and updates status to canceled", async () => {
    const { getByText, queryByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
      expect(getByText("Cancel Request")).toBeTruthy();
    });

    fireEvent.press(getByText("Cancel Request"));

    await waitFor(() => {
      expect(mockedCancelRequest).toHaveBeenCalledWith(PENDING_REQUEST.id);
      expect(getByText("Canceled")).toBeTruthy();
      expect(queryByText("Cancel Request")).toBeNull();
    });
  });

  it("shows cancel error when backend rejects cancellation", async () => {
    mockedCancelRequest.mockRejectedValueOnce(new Error("Request cannot be canceled."));

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Cancel Request")).toBeTruthy();
    });

    fireEvent.press(getByText("Cancel Request"));

    await waitFor(() => {
      expect(getByText("Request cannot be canceled.")).toBeTruthy();
      expect(getByText("Cancel Request")).toBeTruthy();
    });
  });

  it("prevents repeated rapid cancellation taps", async () => {
    let resolveCancel: ((request: FeatureRequestRecord) => void) | null = null;
    mockedCancelRequest.mockImplementationOnce(
      () =>
        new Promise<FeatureRequestRecord>((resolve) => {
          resolveCancel = resolve;
        })
    );

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Cancel Request")).toBeTruthy();
    });

    const cancelButton = getByText("Cancel Request");
    fireEvent.press(cancelButton);
    fireEvent.press(cancelButton);

    expect(mockedCancelRequest).toHaveBeenCalledTimes(1);

    resolveCancel?.({
      ...PENDING_REQUEST,
      status: "canceled"
    });

    await waitFor(() => {
      expect(getByText("Canceled")).toBeTruthy();
    });
  });
});
