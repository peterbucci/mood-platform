import { fireEvent, render, waitFor } from "@testing-library/react-native";

import { createFeatureRequest, getPendingRequestCount, getRequests } from "../api/requests";
import type { FeatureRequestRecord } from "../types/requests";
import RequestsPage from "./RequestsPage";

jest.mock("../api/requests");

const mockedCreateFeatureRequest = jest.mocked(createFeatureRequest);
const mockedGetPendingRequestCount = jest.mocked(getPendingRequestCount);
const mockedGetRequests = jest.mocked(getRequests);

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
    mockedCreateFeatureRequest.mockResolvedValue({
      requestId: "request-created-1",
      status: "pending"
    });
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValue(1);
  });

  it("renders pending, fulfilled, and canceled request statuses", async () => {
    mockedGetRequests.mockResolvedValue([PENDING_REQUEST, FULFILLED_REQUEST, CANCELED_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValue(1);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Pending")).toBeTruthy();
      expect(getByText("Fulfilled")).toBeTruthy();
      expect(getByText("Canceled")).toBeTruthy();
      expect(getByText("Feature ID: feature-fulfilled-1")).toBeTruthy();
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
});
