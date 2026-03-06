import { act, fireEvent, render, waitFor } from "@testing-library/react-native";

import { createFeatureRequest, getPendingRequestCount, getRequests } from "../api/requests";
import type { CreateFeatureRequestResponse, FeatureRequestRecord } from "../types/requests";
import RequestsPage from "./RequestsPage";

jest.mock("../api/requests");

const mockedCreateFeatureRequest = jest.mocked(createFeatureRequest);
const mockedGetPendingRequestCount = jest.mocked(getPendingRequestCount);
const mockedGetRequests = jest.mocked(getRequests);

const BASE_REQUEST: FeatureRequestRecord = {
  createdAt: 1_772_800_000,
  featureId: null,
  id: "request-1",
  source: "fitbit-pipeline",
  status: "pending",
  userId: "00000000-0000-0000-0000-000000000001"
};

describe("RequestsPage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockedCreateFeatureRequest.mockResolvedValue({
      requestId: BASE_REQUEST.id,
      status: "pending"
    });
    mockedGetRequests.mockResolvedValue([]);
    mockedGetPendingRequestCount.mockResolvedValue(0);
  });

  it("submits create request once and shows the new pending request", async () => {
    mockedGetRequests.mockResolvedValueOnce([]).mockResolvedValueOnce([BASE_REQUEST]);
    mockedGetPendingRequestCount.mockResolvedValueOnce(0).mockResolvedValueOnce(1);

    const { getByText, getAllByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Request Feature Capture")).toBeTruthy();
    });

    fireEvent.press(getByText("Request Feature Capture"));

    await waitFor(() => {
      expect(mockedCreateFeatureRequest).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(getAllByText("Status: pending").length).toBeGreaterThan(0);
      expect(getByText("Source: fitbit-pipeline")).toBeTruthy();
      expect(getByText("Pending requests: 1")).toBeTruthy();
    });
  });

  it("prevents duplicate active submissions on rapid taps", async () => {
    let resolveCreate: ((value: CreateFeatureRequestResponse) => void) | null = null;
    const pendingCreate = new Promise<CreateFeatureRequestResponse>((resolve) => {
      resolveCreate = resolve;
    });
    mockedCreateFeatureRequest.mockReturnValueOnce(pendingCreate);

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Request Feature Capture")).toBeTruthy();
    });

    const button = getByText("Request Feature Capture");
    fireEvent.press(button);
    fireEvent.press(button);

    expect(mockedCreateFeatureRequest).toHaveBeenCalledTimes(1);

    act(() => {
      resolveCreate?.({ requestId: "request-2", status: "pending" });
    });

    await waitFor(() => {
      expect(getByText("Request created")).toBeTruthy();
    });
  });

  it("shows an error message when create request fails", async () => {
    mockedCreateFeatureRequest.mockRejectedValueOnce(new Error("Feature request create failed."));

    const { getByText } = render(<RequestsPage />);

    await waitFor(() => {
      expect(getByText("Request Feature Capture")).toBeTruthy();
    });

    fireEvent.press(getByText("Request Feature Capture"));

    await waitFor(() => {
      expect(getByText("Feature request create failed.")).toBeTruthy();
    });
  });
});
