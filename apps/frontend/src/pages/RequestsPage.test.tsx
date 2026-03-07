import { act, fireEvent, render, waitFor, within } from "@testing-library/react-native";
import { useIsFocused, useNavigation } from "@react-navigation/native";

import { getFeatures } from "../api/features";
import {
  createFeatureRequest,
  deleteRequest,
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
const mockedDeleteRequest = jest.mocked(deleteRequest);
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
    mockedDeleteRequest.mockResolvedValue({ id: PENDING_REQUEST.id });
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
      expect(getAllByText("Delete").length).toBeGreaterThan(0);
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

  it("opens a delete confirmation modal with cascading cleanup copy", async () => {
    const { getByTestId, getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("In progress")).toBeTruthy();
      expect(getByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeTruthy();
    });

    fireEvent.press(within(getByTestId(`request-item-${PENDING_REQUEST.id}`)).getByText("Delete"));

    expect(getByText("Delete Request?")).toBeTruthy();
    expect(getByText("This will permanently delete the request.")).toBeTruthy();
    expect(
      getByText("If this request has a linked feature snapshot, it will also be deleted.")
    ).toBeTruthy();
    expect(getByText("Any linked mood labels or related records will also be removed.")).toBeTruthy();
    expect(getByText("This action cannot be undone.")).toBeTruthy();
  });

  it("deletes a request after confirmation and refreshes the list", async () => {
    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST, FULFILLED_REQUEST]).mockResolvedValueOnce([FULFILLED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    const { getByTestId, getByText, queryByTestId } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeTruthy();
    });

    fireEvent.press(within(getByTestId(`request-item-${PENDING_REQUEST.id}`)).getByText("Delete"));
    fireEvent.press(getByTestId("confirm-delete-request-button"));

    await waitFor(() => {
      expect(mockedDeleteRequest).toHaveBeenCalledWith(PENDING_REQUEST.id);
      expect(queryByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeNull();
      expect(getByText("Request deleted successfully.")).toBeTruthy();
    });
  });

  it("shows delete error when backend rejects deletion", async () => {
    mockedDeleteRequest.mockRejectedValueOnce(new Error("Request cannot be deleted."));

    const { getAllByText, getByTestId, getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeTruthy();
    });

    fireEvent.press(within(getByTestId(`request-item-${PENDING_REQUEST.id}`)).getByText("Delete"));
    fireEvent.press(getByTestId("confirm-delete-request-button"));

    await waitFor(() => {
      expect(getByText("Unable to delete request")).toBeTruthy();
      expect(getAllByText("Unable to delete request. Please try again.").length).toBeGreaterThan(
        0
      );
      expect(getByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeTruthy();
    });
  });

  it("prevents repeated rapid deletion confirmations", async () => {
    mockedGetRequests.mockResolvedValueOnce([PENDING_REQUEST]).mockResolvedValueOnce([]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(1).mockResolvedValueOnce(0);

    let resolveDelete:
      | ((value: { id: string } | PromiseLike<{ id: string }>) => void)
      | undefined;
    mockedDeleteRequest.mockImplementationOnce(
      () =>
        new Promise<{ id: string }>((resolve) => {
          resolveDelete = resolve;
        })
    );

    const { getByTestId, queryByTestId } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeTruthy();
    });

    fireEvent.press(within(getByTestId(`request-item-${PENDING_REQUEST.id}`)).getByText("Delete"));

    const confirmDeleteButton = getByTestId("confirm-delete-request-button");
    fireEvent.press(confirmDeleteButton);
    fireEvent.press(confirmDeleteButton);

    expect(mockedDeleteRequest).toHaveBeenCalledTimes(1);

    expect(resolveDelete).toBeDefined();
    resolveDelete?.({ id: PENDING_REQUEST.id });

    await waitFor(() => {
      expect(queryByTestId(`request-item-${PENDING_REQUEST.id}`)).toBeNull();
    });
  });
});
